function showLogin(){
    document.getElementById("loginForm").classList.add("active");
    document.getElementById("regForm").classList.remove("active");
    document.getElementById("loginTab").classList.add("active");
    document.getElementById("regTab").classList.remove("active");
}

function showRegister(){
    document.getElementById("regForm").classList.add("active");
    document.getElementById("loginForm").classList.remove("active");
    document.getElementById("regTab").classList.add("active");
    document.getElementById("loginTab").classList.remove("active");
}
