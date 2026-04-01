const dialog = document.getElementById('myDialog');
const showBtn = document.getElementById('showDialog');
const closeBtn = document.getElementById('closeDialog');

showBtn.addEventListener('click', () => {
    dialog.showModal(); // Показываем как модальное окно (с затемнением)
});

closeBtn.addEventListener('click', () => {
    dialog.close(); // Закрываем
});

// Закрытие по клику вне окна (для dialog)
dialog.addEventListener('click', (event) => {
    const rect = dialog.getBoundingClientRect();
    const isInDialog = (rect.top <= event.clientY && event.clientY <= rect.top + rect.height &&
                         rect.left <= event.clientX && event.clientX <= rect.left + rect.width);
    if (!isInDialog) {
        dialog.close();
    }
});


const dialog1 = document.getElementById('myDialog1');
const showBtn1 = document.getElementById('showDialog1');
const closeBtn1 = document.getElementById('closeDialog1');

showBtn1.addEventListener('click', () => {
    dialog1.showModal(); // Показываем как модальное окно (с затемнением)
});

closeBtn1.addEventListener('click', () => {
    dialog1.close(); // Закрываем
});

// Закрытие по клику вне окна (для dialog)
dialog1.addEventListener('click', (event) => {
    const rect = dialog1.getBoundingClientRect();
    const isInDialog = (rect.top <= event.clientY && event.clientY <= rect.top + rect.height &&
                         rect.left <= event.clientX && event.clientX <= rect.left + rect.width);
    if (!isInDialog) {
        dialog1.close();
    }
});

const dialog2 = document.getElementById('myDialog2');
const showBtn2 = document.getElementById('showDialog2');
const closeBtn2 = document.getElementById('closeDialog2');

showBtn2.addEventListener('click', () => {
    dialog2.showModal(); // Показываем как модальное окно (с затемнением)
});

closeBtn2.addEventListener('click', () => {
    dialog2.close(); // Закрываем
});

// Закрытие по клику вне окна (для dialog)
dialog2.addEventListener('click', (event) => {
    const rect = dialog2.getBoundingClientRect();
    const isInDialog = (rect.top <= event.clientY && event.clientY <= rect.top + rect.height &&
                         rect.left <= event.clientX && event.clientX <= rect.left + rect.width);
    if (!isInDialog) {
        dialog2.close();
    }
});

const dialog3 = document.getElementById('myDialog3');
const showBtn3 = document.getElementById('showDialog3');
const closeBtn3 = document.getElementById('closeDialog3');

showBtn3.addEventListener('click', () => {
    dialog3.showModal(); // Показываем как модальное окно (с затемнением)
});

closeBtn3.addEventListener('click', () => {
    dialog3.close(); // Закрываем
});

// Закрытие по клику вне окна (для dialog)
dialog3.addEventListener('click', (event) => {
    const rect = dialog3.getBoundingClientRect();
    const isInDialog = (rect.top <= event.clientY && event.clientY <= rect.top + rect.height &&
                         rect.left <= event.clientX && event.clientX <= rect.left + rect.width);
    if (!isInDialog) {
        dialog3.close();
    }
});