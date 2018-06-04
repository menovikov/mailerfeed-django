function post(path, params, method) {
  method = method || "post";

  var form = document.createElement("form");
  form.setAttribute("method", method);
  form.setAttribute("action", path);

  for(var key in params) {
      if(params.hasOwnProperty(key)) {
          var hiddenField = document.createElement("input");
          hiddenField.setAttribute("type", "hidden");
          hiddenField.setAttribute("name", key);
          hiddenField.setAttribute("value", params[key]);

          form.appendChild(hiddenField);
      }
  }

  document.body.appendChild(form);
  $.ajax({
      type: "POST",
      url: path,
      dataType: 'jsonp',
      data: $(form).serialize()
    })
}

function sendTrigger(){
  let group_id = parseInt(document.getElementById('vk_subscribe').dataset.client.split("-")[2]);
  let href = 'http://app.mailerfeed.com/vk/users/track/';
  VK.Widgets.AllowMessagesFromCommunity("vk_subscribe", {}, group_id);
  VK.Observer.subscribe("widgets.allowMessagesFromCommunity.allowed", function f(userId) {
    post(href, 
        {
          user_id: userId, 
          allowed: true, 
          client: document.getElementById('vk_subscribe').dataset.client,
        });
  });

  VK.Observer.subscribe("widgets.allowMessagesFromCommunity.denied", function f(userId) {
    post(href, 
        {
          user_id: userId, 
          allowed: false,
          client: document.getElementById('vk_subscribe').dataset.client,
        });
  });
}

if (!document.getElementById('id_jquery_script')) {
  var script = document.createElement('script');
  script.src = "https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js";
  script.id = "id_jquery_script";
  document.getElementsByTagName('head')[0].appendChild(script);
}


if (!document.getElementById('id_vk_script')) {
  var script = document.createElement('script');
  script.src = "https://vk.com/js/api/openapi.js?150";
  script.id = "id_vk_script";
  document.getElementsByTagName('head')[0].appendChild(script);
  script.onload = sendTrigger;
} else {
  sendTrigger();
}