function getBathValue() {
  var uiBathrooms = document.getElementsByName("uiBathrooms");
  for(var i in uiBathrooms) {
    if(uiBathrooms[i].checked) {
        return parseInt(i)+1;
    }
  }
  return -1; // Invalid Value
}

function getBHKValue() {
  var uiBHK = document.getElementsByName("uiBHK");
  for(var i in uiBHK) {
    if(uiBHK[i].checked) {
        return parseInt(i)+1;
    }
  }
  return -1; // Invalid Value
}

function onClickedEstimatePrice() {
  console.log("Estimate price button clicked");
  var sqft = document.getElementById("uiSqft");
  var bhk = getBHKValue();
  var bathrooms = getBathValue();
  var location = document.getElementById("uiLocations");
  var estPrice = document.getElementById("uiEstimatedPrice");

  var url = "http://127.0.0.1:5000/predict_home_price"; //Use this if you are NOT using nginx which is first 7 tutorials//
  
  $.post(url, {
      total_sqft: parseFloat(sqft.value),
      bhk: bhk,
      bath: bathrooms,
      location: location.value
  },function(data, status) {
      console.log(data.estimated_price);
      estPrice.innerHTML = "<h2>" + data.estimated_price.toString() + " Lakh</h2>";
      console.log(status);
  });
}

function onPageLoad() {
  console.log( "document loaded" );
   var url = "http://127.0.0.1:5000/get_location_names"; // Use this if you are NOT using nginx which is first 7 tutorials//
  
  $.get(url,function(data, status) {
      console.log("got response for get_location_names request");
      if(data) {
          var locations = data.locations;
          var uiLocations = document.getElementById("uiLocations");
          $('#uiLocations').empty();
          for(var i in locations) {
              var opt = new Option(locations[i]);
              $('#uiLocations').append(opt);
          }
      }
  });
}
function onClickedEstimateFuturePrice() {
  var sqft = document.getElementById("uiSqft").value;
  var bhk = getBHKValue();
  var bathrooms = getBathValue();
  var location = document.getElementById("uiLocations").value;
  var horizon = document.getElementById("uiHorizon").value || 12;  // months

  var url = "http://127.0.0.1:5000/predict_future_price";

  $.ajax({
    url: url,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      total_sqft: parseFloat(sqft),
      bhk: bhk,
      bath: bathrooms,
      location: location,
      horizon_months: parseInt(horizon)
    }),
    success: function(data) {
      document.getElementById("uiEstimatedCurrent").innerHTML = "<h4>Current: ₹ " + data.current_price + "</h4>";
      document.getElementById("uiEstimatedFuture").innerHTML = "<h4>In " + horizon + " months: ₹ " + data.future_price + "</h4>";
      document.getElementById("uiRisk").innerHTML = "<p>Risk: " + data.risk + " (" + data.expected_growth_percent + "%)</p>";
      document.getElementById("uiRecommendation").innerHTML = "<b>Action: " + data.recommendation + "</b>";
    },
    error: function(xhr, status, err) {
      console.error(err);
      alert("Error getting future prediction: " + err);
    }
  });
}

window.onload = onPageLoad;