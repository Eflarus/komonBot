/**
 * Contact Form Script for Ghost CMS
 *
 * Usage:
 *   1. In Ghost editor, add an HTML card where you want the form:
 *      <div id="call-contact-form">Оставить заявку</div>
 *
 *   2. In Ghost Code Injection (Site Footer), add:
 *      <script src="/path/to/contact-form.js"></script>
 *      or paste the contents of this file inside <script> tags.
 *
 *   The form can either be pre-rendered in an HTML card (Ghost will
 *   display it immediately) or injected dynamically on click.
 *   The script detects both cases automatically.
 *
 * Configuration:
 *   Set CONTACT_FORM_API_URL before loading the script to override
 *   the default API URL:
 *     <script>var CONTACT_FORM_API_URL = 'https://example.com/bot/api/contacts';</script>
 */
(function () {
  var API_URL =
    window.CONTACT_FORM_API_URL ||
    "https://komon.tot.pub/bot179654/api/contacts";

  var FORM_HTML =
    '<div class="wrap">' +
    '  <div class="feedback-card form-card" style="position: relative;">' +
    '    <button type="button" class="form-close" aria-label="Закрыть"' +
    '      style="position:absolute;top:12px;right:12px;background:none;border:none;' +
    '      font-size:24px;line-height:1;cursor:pointer;color:inherit;padding:4px 8px;">' +
    "      &times;" +
    "    </button>" +
    "    <h5>ЗАПОЛНИТЕ ФОРМУ И&nbsp;МЫ <br>ВАМ ПЕРЕЗВОНИМ</h5>" +
    '    <form class="contact-feedback-form">' +
    '      <input name="name" placeholder="Имя" required maxlength="100">' +
    '      <input name="phone" placeholder="Телефон" required inputmode="tel">' +
    '      <textarea name="message" placeholder="Сообщение" required maxlength="1000"></textarea>' +
    '      <input name="website" type="text" style="display:none" tabindex="-1" autocomplete="off">' +
    '      <button type="submit">Отправить</button>' +
    "    </form>" +
    "  </div>" +
    '  <div class="feedback-card thanks-card" style="display: none;">' +
    '    <h5 style="text-align: center">СПАСИБО!</h5>' +
    '    <h5 style="text-align: center">Мы свяжемся с&nbsp;вами<br>в ближайшее время.</h5>' +
    "  </div>" +
    "</div>";

  function showError(el, msg) {
    clearError(el);
    var div = document.createElement("div");
    div.className = "form-error";
    div.textContent = msg;
    el.parentNode.insertBefore(div, el.nextSibling);
    el.style.borderColor = "#dc3545";
  }

  function clearError(el) {
    var next = el.nextElementSibling;
    if (next && next.classList.contains("form-error")) next.remove();
    el.style.borderColor = "";
  }

  function initForm(container) {
    var form = container.querySelector("form");
    var btn = container.querySelector('button[type="submit"]');
    if (!form || !btn) return;

    // Close button — always register re-open handler for pre-rendered forms
    var closeBtn = container.querySelector(".form-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        container.innerHTML = "Оставить заявку";
        container.classList.remove("form-rendered");
        container.addEventListener("click", function reopen() {
          container.removeEventListener("click", reopen);
          container.innerHTML = FORM_HTML;
          container.classList.add("form-rendered");
          initForm(container);
        });
      });
    }

    // Phone mask: +_ (___) ___-__-__
    // Matrix approach with inputType detection for backspace over formatting chars
    var phoneInput = form.querySelector('[name="phone"]');
    if (phoneInput) {
      var MASK = "+_ (___) ___-__-__";
      var prevDigits = 0;

      function applyMask(digits) {
        var i = 0;
        phoneInput.value = MASK.replace(/./g, function (ch) {
          return ch === "_" && i < digits.length ? digits[i++] : ch;
        });
        var cursorPos = phoneInput.value.indexOf("_");
        if (cursorPos === -1) cursorPos = phoneInput.value.length;
        phoneInput.setSelectionRange(cursorPos, cursorPos);
        prevDigits = digits.length;
      }

      phoneInput.addEventListener("input", function (e) {
        var digits = phoneInput.value.replace(/\D/g, "").substring(0, 11);

        // Backspace landed on a formatting char — digit count unchanged, force drop one
        var isDel = e.inputType === "deleteContentBackward" ||
          e.inputType === "deleteContentForward";
        if (isDel && digits.length >= prevDigits && prevDigits > 0) {
          digits = digits.substring(0, digits.length - 1);
        }

        if (!digits) {
          phoneInput.value = "";
          prevDigits = 0;
          return;
        }
        applyMask(digits);
      });

      phoneInput.addEventListener("focus", function () {
        var digits = phoneInput.value.replace(/\D/g, "").substring(0, 11);
        applyMask(digits);
      });

      phoneInput.addEventListener("blur", function () {
        if (!phoneInput.value.replace(/\D/g, "")) {
          phoneInput.value = "";
          prevDigits = 0;
        }
      });
    }

    form.querySelectorAll("input:not([type='hidden']), textarea").forEach(
      function (el) {
        el.addEventListener("input", function () {
          clearError(el);
        });
      },
    );

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearError(btn);
      var fd = new FormData(form);
      var rawPhone = (fd.get("phone") || "").replace(/\D/g, "");
      var data = {
        name: (fd.get("name") || "").trim(),
        phone: rawPhone ? "+" + rawPhone : "",
        message: (fd.get("message") || "").trim(),
        website: fd.get("website") || undefined,
        source: "site",
      };

      var valid = true;
      if (data.name.length < 2) {
        showError(
          form.querySelector('[name="name"]'),
          "Минимум 2 символа",
        );
        valid = false;
      }
      if (!/^\+?\d{7,15}$/.test(data.phone)) {
        showError(
          form.querySelector('[name="phone"]'),
          "Введите корректный номер",
        );
        valid = false;
      }
      if (data.message.length < 5) {
        showError(
          form.querySelector('[name="message"]'),
          "Минимум 5 символов",
        );
        valid = false;
      }
      if (!valid) return;

      btn.disabled = true;
      btn.textContent = "Отправляем...";

      fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then(function (res) {
          if (!res.ok) throw new Error();

          var formCard = container.querySelector(".form-card");
          var thanksCard = container.querySelector(".thanks-card");
          if (formCard) formCard.style.display = "none";
          if (thanksCard) thanksCard.style.display = "block";

          setTimeout(function () {
            container.innerHTML = "Оставить заявку";
            container.classList.remove("form-rendered");
          }, 5000);
        })
        .catch(function () {
          showError(btn, "Ошибка отправки. Попробуйте ещё раз.");
          btn.disabled = false;
          btn.textContent = "Отправить";
        });
    });
  }

  function init() {
    var el = document.getElementById("call-contact-form");
    if (!el) return;

    // Form already rendered in Ghost HTML card — init immediately
    if (el.querySelector("form")) {
      initForm(el);
      return;
    }

    // Otherwise — show form on click
    el.addEventListener("click", function (e) {
      if (el.classList.contains("form-rendered")) return;
      e.preventDefault();
      el.innerHTML = FORM_HTML;
      el.classList.add("form-rendered");
      initForm(el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
