const queue: Array<() => void> = [];
let running = false;
const INTERVAL_MS = 1000;

export function withRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const execute = async () => {
      running = true;
      try {
        resolve(await fn());
      } catch (e) {
        reject(e);
      } finally {
        setTimeout(() => {
          running = false;
          const next = queue.shift();
          if (next) next();
        }, INTERVAL_MS);
      }
    };

    if (!running) {
      execute();
    } else {
      queue.push(execute);
    }
  });
}
