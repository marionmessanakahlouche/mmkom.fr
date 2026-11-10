const dialog = document.querySelector('#contact-dialog');
const emailField = dialog?.querySelector('.contact-email');
let contactTrigger;

if (dialog && emailField && typeof dialog.showModal === 'function') {
  emailField.addEventListener('click', () => emailField.select());

  document.querySelectorAll(`a[href="mailto:${emailField.value}"]`).forEach(link => {
    link.setAttribute('aria-haspopup', 'dialog');
    link.setAttribute('aria-controls', 'contact-dialog');
    link.addEventListener('click', event => {
      event.preventDefault();
      contactTrigger = link;
      dialog.showModal();
      dialog.querySelector('.dialog-close').focus();
    });
  });

  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => contactTrigger?.focus());

  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) {
      dialog.close();
    }
  });
}

const ribbonToggle = document.querySelector('.ribbon-toggle');
const ribbon = document.querySelector('.ribbon');
if (ribbonToggle && ribbon) {
  ribbonToggle.hidden = false;
  ribbonToggle.addEventListener('click', () => {
    const paused = ribbon.classList.toggle('is-paused');
    ribbonToggle.setAttribute('aria-pressed', String(paused));
    const label = paused ? 'Reprendre le défilement' : 'Mettre le bandeau en pause';
    ribbonToggle.setAttribute('aria-label', label);
    ribbonToggle.title = label;
  });
}
