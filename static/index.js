const signupBtn = document.getElementById("signup-btn");
const loginBtn = document.getElementById("login-btn");
const accountBtn = document.getElementById("account");
const logoutBtn = document.getElementById("logout-btn");
const sponsoredBtn = document.getElementById("sponsored-btn");

sponsoredBtn.addEventListener("click", () => location.assign("/sponsor"));

if (loginBtn != undefined && signupBtn != undefined) {
    loginBtn.addEventListener("click", () => location.assign("/login"));
    signupBtn.addEventListener("click", () => location.assign("/signup"));
};
if (logoutBtn != undefined) {
    logoutBtn.addEventListener("click", () => location.assign("/logout"));
};
accountBtn.addEventListener("click", () => location.assign("/dashboard"));

const currentPageText = document.getElementById("current-page");
const rowsPerPage = 25;
pageIndex = 1;
totalRows = 0;

function switchToPage(page) {
    if (page == pageIndex || page < 1 || page > Math.ceil(totalRows / rowsPerPage)) return;
    pageIndex = page;
    currentPageText.innerText = "Page " + pageIndex;
    createTableContents();
};

document.getElementById("first-page").addEventListener("click", () => switchToPage(1));
document.getElementById("prev-page").addEventListener("click", () => switchToPage(pageIndex - 1));
document.getElementById("next-page").addEventListener("click", () => switchToPage(pageIndex + 1));
document.getElementById("last-page").addEventListener("click", () => switchToPage(Math.ceil(totalRows / rowsPerPage)));

const serverTableBody = document.getElementById("server-table-body");
function addServerToTable(serverRow, serverContent) {
    let newCell = serverRow.insertCell();
    let newText = document.createTextNode(serverContent);
    newCell.appendChild(newText);
};

function createTableContents() {
    fetch("/servers")
    .then((response) => response.json())
    .then((json) => {
        serverTableBody.innerHTML = "";
        totalRows = json.length;
        startIndex = (pageIndex-1) * rowsPerPage;
        for (server of json.slice(startIndex, startIndex+rowsPerPage)) {
            let newServerRow = serverTableBody.insertRow();
            addServerToTable(newServerRow, server["Rank"]);
            let iconCell = newServerRow.insertCell();
            let iconImage = document.createElement("img");
            iconString = "https://eu.mc-api.net/v3/server/favicon/" + server["IP"]
            fetch(iconString)
            .then(response => response.blob())
            .then(blob => {
                let reader = new FileReader();
                reader.onload = () => {
                    iconImage.src = reader.result;
                };
                reader.readAsDataURL(blob);
            })
            .catch(error => {
                console.error("Error fetching icon:", error);
                addServerToTable(newServerRow, server["Name"]); 
            });
            iconImage.alt = "Server Icon";
            iconCell.appendChild(iconImage);
            addServerToTable(newServerRow, server["Server"]); 
            addServerToTable(newServerRow, server["Players"]);
            addServerToTable(newServerRow, server["IP"]);
            
        };
    });
};
createTableContents();