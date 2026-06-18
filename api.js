function getRequests(){
  return JSON.parse(localStorage.getItem("requests")) || [];
}

function addRequest(req){
  let data = getRequests();
  data.push(req);
  localStorage.setItem("requests", JSON.stringify(data));
}

function clearRequests(){
  localStorage.removeItem("requests");
}