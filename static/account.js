document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.querySelector('.nav__toggle-btn');
    const navLinks = document.querySelector('.nav__links');
  
    toggleBtn.addEventListener('click', function () {
      navLinks.classList.toggle('active');
    });
  });