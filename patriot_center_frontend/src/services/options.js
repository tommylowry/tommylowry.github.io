export async function fetchOptions() {
    const res = await fetch('/meta/options');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  }