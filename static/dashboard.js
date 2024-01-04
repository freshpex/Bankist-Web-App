function toggleBalance(button) {
  var targetId = button.getAttribute("data-target");
  var target = document.getElementById(targetId);
  if (target.style.display === "none") {
    target.style.display = "inline";
    button.innerHTML = "<i class='fa fa-eye'></i>";
  } else {
    target.style.display = "none";
    button.innerHTML = "<i class='fa fa-eye-slash'></i>";
  }
}

document.addEventListener('DOMContentLoaded', function () {
  function updateCurrentDate() {
    const currentDateElement = document.getElementById('currentDate');
    const currentDate = new Date();

    const formattedDate = `${currentDate.getMonth() + 1}/${currentDate.getDate()}/${currentDate.getFullYear()}`;

    currentDateElement.textContent = formattedDate;
  }

  updateCurrentDate();    
  setInterval(updateCurrentDate, 1000);
});

document.getElementById('transaction_type').addEventListener('change', function() {
  var internationalFields = document.getElementById('international_fields');
  if (this.value === 'international') {
      internationalFields.style.display = 'block';
  } else {
      internationalFields.style.display = 'none';
  }
});

document.querySelector('.form--transfer').addEventListener('submit', function (event) {
event.preventDefault();

var formData = new FormData(this);

fetch('/process_transaction', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        document.getElementById('transactionMessage').innerHTML = 'Transaction successful. Reloading page...';
        setTimeout(function () {
            location.reload();
        }, 2000); 
    } else {
        document.getElementById('transactionMessage').innerHTML = 'Transaction failed: ' + data.error;
    }
})
.catch(error => {
    console.error('Error during fetch:', error);
});
});

document.querySelector('.form--loan').addEventListener('submit', function (event) {
event.preventDefault();

var formData = new FormData(this);

fetch('/request_loan', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        document.getElementById('loanMessage').innerHTML = 'Loan request successful. Reloading page...';
        setTimeout(function () {
            location.reload();
        }, 2000);
    } else {
        document.getElementById('loanMessage').innerHTML = 'Loan request failed: ' + data.error;
    }
})
.catch(error => {
    console.error('Error during fetch:', error);
});
});  

document.addEventListener('DOMContentLoaded', function () {
const toggleBtn = document.querySelector('.nav__toggle-btn');
const navLinks = document.querySelector('.nav__links');

toggleBtn.addEventListener('click', function () {
  navLinks.classList.toggle('active');
});
});