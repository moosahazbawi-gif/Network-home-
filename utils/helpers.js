function formatDate(date){
  return new Date(date).toLocaleString();
}

function saveToStorage(key, data){
  localStorage.setItem(key, JSON.stringify(data));
}

function getFromStorage(key){
  return JSON.parse(localStorage.getItem(key)) || [];
}