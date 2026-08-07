var nm1 = ["", "", "", "", "", "b", "d", "f", "g", "h", "l", "n", "p", "ph", "ps", "r", "v", "y"];
var nm2 = ["oo", "ee", "aa", "a", "e", "i", "o", "y", "a", "e", "i", "o", "y", "u", "a", "e", "i", "o", "y"];
var nm3 = ["b", "bl", "d", "g", "gl", "gr", "l", "lb", "ld", "p", "r", "rb", "s", "sb", "sh", "st"];
var nm4 = ["a", "e", "i", "o"];
var nm5 = ["b", "c", "d", "l", "m", "n", "p", "r", "b", "c", "d", "l", "m", "n", "p", "r", "b", "c", "d", "l", "m", "n", "p", "r", "bl", "br", "dr", "pb", "pl", "pr", "rb", "rd", "sn", "sp"];
var nm6 = ["ia", "oo", "aa", "io", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u"];
var nm7 = ["", "b", "d", "l", "p", "r", "s", "b", "d", "l", "p", "r", "s"];

var br = "";

function nameGen(type) {
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var element = document.createElement("div");
	element.setAttribute("id", "result");

	for (i = 0; i < 10; i++) {
		nameMas();
		while (nMs === "") {
			nameMas();
		}
		br = document.createElement('br');
		element.appendChild(document.createTextNode(nMs));
		element.appendChild(br);
	}
	if (document.getElementById("result")) {
		document.getElementById("placeholder").removeChild(document.getElementById("result"));
	}
	document.getElementById("placeholder").appendChild(element);
}

function nameFem() {
	nTp = Math.random() * 7 | 0;
	rnd = Math.random() * nm8.length | 0;
	rnd2 = Math.random() * nm9.length | 0;
	rnd3 = Math.random() * nm10.length | 0;
	rnd4 = Math.random() * nm14.length | 0;
	rnd7 = Math.random() * nm15.length | 0;
	if (nTp < 4) {
		while (nm10[rnd3] === nm8[rnd] || nm10[rnd3] === nm15[rnd7]) {
			rnd3 = Math.random() * nm10.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm14[rnd4] + nm15[rnd7];
	} else {
		rnd5 = Math.random() * nm11.length | 0;
		rnd6 = Math.random() * nm12.length | 0;
		while (nm12[rnd6] === nm10[rnd3] || nm10[rnd3] === nm8[rnd]) {
			rnd3 = Math.random() * nm10.length | 0;
		}
		if (nTp < 6) {
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd5] + nm12[rnd6] + nm14[rnd4] + nm15[rnd7];
		} else {
			rnd8 = Math.random() * nm11.length | 0;
			rnd9 = Math.random() * nm13.length | 0;
			while (nm12[rnd6] === nm13[rnd9] || nm13[rnd9] === nm15[rnd7]) {
				rnd9 = Math.random() * nm13.length | 0;
			}
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd5] + nm12[rnd6] + nm11[rnd8] + nm13[rnd9] + nm14[rnd4] + nm15[rnd7];
		}
	}
}

function nameMas() {
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm7.length | 0;
	rnd4 = Math.random() * nm3.length | 0;
	rnd5 = Math.random() * nm4.length | 0;
	if (nTp < 3) {
		while (nm3[rnd4] === nm1[rnd] || nm3[rnd4] === nm7[rnd3]) {
			rnd4 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm4[rnd5] + nm7[rnd3];
	} else {
		rnd6 = Math.random() * nm5.length | 0;
		rnd7 = Math.random() * nm6.length | 0;
		while (nm3[rnd4] === nm5[rnd6] || nm5[rnd6] === nm7[rnd3]) {
			rnd6 = Math.random() * nm5.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm4[rnd5] + nm5[rnd6] + nm6[rnd7] + nm7[rnd3];
	}
}
