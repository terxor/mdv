window.renderMath = function (container) {
  const unescapeLatex = (text) => text.replace(/\\\\/g, '\\');

  // Inline math
  container.querySelectorAll('.math.inline').forEach((el) => {
    katex.render(unescapeLatex(el.textContent), el, {
      throwOnError: false,
      displayMode: false,
    });
  });

  // Block math
  container.querySelectorAll('.math.block').forEach((el) => {
    katex.render(unescapeLatex(el.textContent), el, {
      throwOnError: false,
      displayMode: true,
    });
  });
}
