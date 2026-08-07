var nm1 = ["","","","","","b","d","g","jh","k","l","m","n","r","s","sh","t","tr","th","thr","v"];
var nm2 = ["a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","aa","ae","ao","au"];
var nm3 = ["ch","d","dr","dh","g","gr","gh","gg","l","ll","lt","lth","lr","p","r","rg","rht","rk","rt","rd","rth","sh","sk","shr","sh","sl","t","th","tr","thr"];
var nm4 = ["a","e","i","o","u","y","a","e","i","o","u","y","a","e","i","o","u","y","a","e","i","o","u","y","a","e","i","o","u","y","a","e","i","o","u","y","a","e","i","o","u","a","e","i","o","u","ea","ua","ae","ia","aa","ao"];
var nm5 = ["c","g","gr","gn","k","kh","kr","r","rr","s","ss","sr","st","str","t","th","tr"];
var nm6 = ["","","","","","","","ch","k","n","nd","nk","nt","r","rd","rk","rt","rth","s","ss","sh","sj","sk","t","th","v","x"];
var nm7 = ["Achiever","Advantage","Adventure","Air","Alarm","Ambition","Anger","Animal","Answer","Anxiety","Armor","Art","Artist","Author","Axe","Badge","Bait","Balance","Ball","Bank","Battle","Beach","Bead","Beam","Bean","Bear","Beast","Beetle","Beginning","Bell","Belt","Bird","Bite","Bitter","Black","Blade","Blood","Board","Bone","Book","Boot","Border","Bother","Bowl","Brain","Brass","Brave","Bravery","Bread","Breath","Burn","Button","Camp","Cart","Cash","Catch","Cave","Cell","Chain","Chalk","Challenge","Champion","Chance","Change","Chaos","Chest","Choice","Clever","Cloud","Clue","Comfort","Courage","Creative","Crimson","Crown","Cub","Curiosity","Dance","Danger","Dark","Demon","Desire","Dexterity","Diamond","Direction","Dirt","Double","Dragon","Dream","Earth","Edge","Effect","Elegance","Emerald","Emotion","Emphasis","Envy","Error","Eternity","Eye","Faith","Fall","Family","Fang","Farm","Fear","Feast","Fight","Final","Fire","Flame","Flight","Flower","Fluke","Force","Forever","Fortune","Freedom","Friend","Gem","Generous","Ghost","Gold","Good","Green","Guide","Habit","Half","Hammer","Happiness","Happy","Harmony","Hate","Heart","Hearth","Home","Honor","Horn","Ice","Icicle","Imagination","Impulse","Ink","Insect","Intelligent","Iron","Journey","Judgement","Justice","Kind","Kindness","Knowledge","Lesson","Liberty","Lie","Life","Light","Limit","Locket","Love","Many","Marble","Mark","Mask","Match","Memory","Mercy","Middle","Midnight","Might","Miracle","Misery","Mist","Moment","Moon","Mountain","Muscle","Nerve","Night","Nobody","Nothing","Omen","Orange","Paint","Paste","Patch","Patience","Patient","Piece","Pitch","Pleasure","Plenty","Pocket","Power","Pride","Promise","Prompt","Push","Question","Quick","Rabbit","Rain","Rainstorm","Range","Reason","Red","Relief","Reserve","Respect","Rest","Riches","Riddle","Ring","Risk","Rose","Rumor","Sanguine","Scent","Scratch","Secret","Sense","Serene","Shade","Shadow","Shell","Shock","Shot","Sign","Signal","Silver","Single","Skill","Sky","Sleep","Slice","Slide","Small","Smart","Smash","Smile","Smoke","Snow","Snowflake","Song","Sorrow","Spark","Sparkle","Spell","Spider","Spirit","Spite","Split","Steel","Stick","Stitch","Stock","Storm","Strength","Strike","Struggle","Tackle","Talent","Tell","Temper","Theory","Thicket","Thing","Thrill","Thunder","Tired","Tolerance","Tool","Travel","Trick","Trust","Truth","Tune","Twist","Victory","Village","Visitor","Voice","Voyage","Walk","War","Watch","Wave","Wealth","Welcome","Whole","Will","Wisdom","Wish","Wistle","Wonder","Wrath"];

var br = "";

function nameGen(type){
	var tp = type;
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");

	for(i = 0; i < 10; i++){
		if(tp === 1){
			rnd = Math.random() * nm7.length | 0;
			nMs = nm7[rnd];
			nm7.splice(rnd, 1);
		}else{
			nameMas();
			while(nMs === ""){
				nameMas();
			}
		}
		br = document.createElement('br');	
		element.appendChild(document.createTextNode(nMs));
		element.appendChild(br);
	}
	if(document.getElementById("result")){
		document.getElementById("placeholder").removeChild(document.getElementById("result"));
	}		
	document.getElementById("placeholder").appendChild(element);
}

function nameMas(){
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm6.length | 0;
	if(i < 2){
		if(rnd < 5){
			while(nm6[rnd3] === nm1[rnd]){
				rnd3 = Math.random() * nm6.length | 0;
			}
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm6[rnd3];
	}else{
		rnd4 = Math.random() * nm3.length | 0;
		rnd5 = Math.random() * nm4.length | 0;
		while(nm3[rnd4] === nm1[rnd] || nm3[rnd4] === nm6[rnd3]){
			rnd4 = Math.random() * nm3.length | 0;
		}
		if(i < 7){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm4[rnd5] + nm6[rnd3];
		}else{
			rnd6 = Math.random() * nm2.length | 0;
			rnd7 = Math.random() * nm5.length | 0;
			while(nm5[rnd7] === nm3[rnd4] || nm5[rnd7] === nm6[rnd3]){
				rnd7 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm2[rnd6] + nm5[rnd7] + nm4[rnd5] + nm6[rnd3];
		}
	}
	
	testSwear(nMs);
}