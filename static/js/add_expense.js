let selected = new Set();

function addMember(uid, name){
    if(selected.has(uid)) return;
    selected.add(uid);

    let chip = document.createElement("div");
    chip.className = "chip";
    chip.innerText = name + " ✕";

    chip.onclick = () => removeMember(uid, chip);

    let input = document.createElement("input");
    input.type = "hidden";
    input.name = "members";     // backend reads this
    input.value = uid;

    chip.appendChild(input);
    document.getElementById("selectedMembers").appendChild(chip);
}

function removeMember(uid, el){
    selected.delete(uid);
    el.remove();
}

function filterMembers(q){
    q = q.toLowerCase().trim();
    document.querySelectorAll(".member-row").forEach(m=>{
        m.style.display = m.innerText.toLowerCase().includes(q) ? "block" : "none";
    });
}

/* Attach ONLY to the expense form */
document.getElementById("expenseForm").addEventListener("submit", function(e){
    if(selected.size < 2){
        alert("Select at least 2 members");
        e.preventDefault();
    }
});
