const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const { setImmediate } = require("node:timers/promises");

class Element {
  constructor() {
    this.children = [];
    this.value = "";
    this.textContent = "";
    this.classList = { add() {}, remove() {} };
  }

  appendChild(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
  set innerHTML(value) { this.html = value; this.children = []; }
  get options() { return this.children; }
  setAttribute() {}
  addEventListener(event, handler) { this[event] = handler; }
}

function setup() {
  const elements = {
    "activities-list": new Element(),
    activity: new Element(),
    "signup-form": new Element(),
    message: new Element(),
    email: new Element(),
  };
  elements.activity.appendChild(new Element());
  elements["signup-form"].reset = () => {
    elements.email.value = "";
    elements.activity.value = "";
  };

  const reads = [];
  const cache = {};
  const fetch = (url, options) => {
    if (options?.method === "POST") {
      return Promise.resolve({ ok: true, json: async () => ({ message: "Signed up" }) });
    }
    return new Promise((resolve) => reads.push({ options, resolve, cache }));
  };
  const document = {
    getElementById: (id) => elements[id],
    createElement: () => new Element(),
    addEventListener: (_, handler) => handler(),
  };
  const source = fs.readFileSync(path.join(__dirname, "../src/static/app.js"), "utf8");
  vm.runInNewContext(source, { document, fetch, console, setTimeout() {} });
  return { elements, reads };
}

function respond(read, participants) {
  if (read.options?.cache !== "no-store") {
    read.cache.participants ??= participants;
    participants = read.cache.participants;
  }
  read.resolve({
    ok: true,
    json: async () => ({
      Chess: {
        description: "Chess",
        schedule: "Friday",
        max_participants: 4,
        participants,
      },
    }),
  });
}

function participantNames(elements) {
  const participants = elements["activities-list"].children[0].children[0];
  return participants.children[1].children.map((row) => row.children[0].textContent);
}

test("signup refreshes participant list and availability without reloading", async () => {
  const { elements, reads } = setup();
  respond(reads[0], ["first@example.com"]);
  await setImmediate();
  elements.email.value = "second@example.com";
  elements.activity.value = "Chess";
  const signup = elements["signup-form"].submit({ preventDefault() {} });
  await setImmediate();
  respond(reads[1], ["first@example.com", "second@example.com"]);
  await signup;

  assert.deepEqual(participantNames(elements), ["first@example.com", "second@example.com"]);
  assert.match(elements["activities-list"].children[0].html, /2 spots left/);
  assert.equal(elements.activity.children.length, 2);
});

test("an older refresh cannot overwrite a newer signup", async () => {
  const { elements, reads } = setup();
  respond(reads[0], ["first@example.com"]);
  await setImmediate();

  elements.email.value = "second@example.com";
  elements.activity.value = "Chess";
  const firstSignup = elements["signup-form"].submit({ preventDefault() {} });
  await setImmediate();

  elements.email.value = "third@example.com";
  elements.activity.value = "Chess";
  const secondSignup = elements["signup-form"].submit({ preventDefault() {} });
  await setImmediate();
  respond(reads[2], ["first@example.com", "second@example.com", "third@example.com"]);
  await secondSignup;
  respond(reads[1], ["first@example.com", "second@example.com"]);
  await firstSignup;

  assert.deepEqual(participantNames(elements), [
    "first@example.com",
    "second@example.com",
    "third@example.com",
  ]);
});
