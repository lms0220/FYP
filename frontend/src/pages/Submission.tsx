import { useState } from "react";
import {
  Shield,
  MessageSquare,
  Link as LinkIcon,
  Search,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { predictText } from "../api";


interface Example {
  id: number;
  label: string;
  description: string;
  content: string;
  type: "sms" | "url";
  expectedResult: "SAFE" | "SCAM";
}


const safeExamples: Example[] = [
  {
    id: 1,
    label: "Trusted Website",
    description: "A legitimate HTTPS website",
    content: "https://www.microsoft.com",
    type: "url",
    expectedResult: "SAFE",
  },

  {
    id: 2,
    label: "Bank Verification SMS",
    description: "Normal OTP verification message",
    content:
      "Your bank verification code is 847392. Do not share this code with anyone.",
    type: "sms",
    expectedResult: "SAFE",
  },

];


const maliciousExamples: Example[] = [

  {
    id: 3,
    label: "Fake Bank Login",
    description:
      "Phishing website pretending to be a bank",
    content:
      "http://secure-bank-login.xyz/verify/account",
    type:"url",
    expectedResult:"SCAM",
  },


  {
    id:4,
    label:"Amazon Account Scam",
    description:
      "Fake SMS requesting account verification",
    content:
      "URGENT: Your Amazon account is suspended. Verify now: http://amaz0n-login.ru",
    type:"sms",
    expectedResult:"SCAM",
  },


];



export default function Submission(){

const navigate = useNavigate();


const [activeTab,setActiveTab]
=
useState<"sms"|"url">("sms");


const [input,setInput]
=
useState("");


const [loading,setLoading]
=
useState(false);


const [loadedExample,setLoadedExample]
=
useState<Example|null>(null);



const instructions={

sms:
"Paste suspicious SMS messages. AI will detect phishing patterns and scam behaviour.",


url:
"Paste a URL. AI will analyse domain reputation, URL patterns and phishing indicators."

};



const handleExampleClick=(example:Example)=>{

setActiveTab(example.type);

setInput(example.content);

setLoadedExample(example);

};



const handleAnalyze=async()=>{


if(!input.trim()){

alert(
`Please enter ${
activeTab==="sms"
?"SMS message"
:"URL"
}`
);

return;

}



if(activeTab==="url" && 
!input.includes("."))
{

alert("Please enter a valid URL");

return;

}



try{


setLoading(true);



const result =
await predictText(input);



if(!result){

throw new Error(
"No result returned"
);

}



const resultId =
crypto.randomUUID
?
crypto.randomUUID()
:
Date.now().toString();



sessionStorage.setItem(

`scamShieldResult-${resultId}`,

JSON.stringify({

result,

content:input

})

);



navigate(

`/app/results/${resultId}`,

{

state:{

result,

content:input

}

}

);



}

catch(error){


console.error(error);


alert(

error instanceof Error
?
error.message
:
"Backend connection failed"

);


}

finally{

setLoading(false);

}


};



return (

<div className="max-w-6xl mx-auto space-y-8">



{/* HEADER */}

<div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-2xl p-8 text-white shadow-lg">


<h1 className="text-4xl font-bold">

Scam & Phishing Detection

</h1>


<p className="mt-2 text-indigo-100">

AI-powered SMS and URL security analysis

</p>


</div>





{/* TAB */}

<div className="bg-white rounded-xl shadow overflow-hidden">


<div className="flex border-b">


<button

onClick={()=>{

setActiveTab("sms");

setInput("");

setLoadedExample(null);

}}

className={`flex-1 p-4 font-semibold flex justify-center gap-2

${activeTab==="sms"
?
"bg-indigo-600 text-white"
:
"bg-gray-50"}

`}

>

<MessageSquare size={20}/>

SMS Analysis

</button>




<button

onClick={()=>{

setActiveTab("url");

setInput("");

setLoadedExample(null);

}}

className={`flex-1 p-4 font-semibold flex justify-center gap-2

${activeTab==="url"
?
"bg-indigo-600 text-white"
:
"bg-gray-50"}

`}

>


<LinkIcon size={20}/>

URL Analysis


</button>


</div>






<div className="p-8 space-y-6">


<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">

<p className="text-blue-900">

{instructions[activeTab]}

</p>

</div>





<label className="font-semibold">

{
activeTab==="sms"
?
"SMS Message"
:
"URL"

}

</label>



<textarea


value={input}


onChange={(e)=>{


setInput(e.target.value);


if(e.target.value!==loadedExample?.content){

setLoadedExample(null);

}


}}


className="w-full h-56 border-2 rounded-lg p-4 font-mono"


placeholder={

activeTab==="sms"
?
"Enter SMS..."
:
"Enter URL..."

}


/>





{loadedExample && (

<div className={`p-3 rounded-lg flex gap-2

${loadedExample.expectedResult==="SAFE"
?
"bg-green-50 text-green-700"
:
"bg-red-50 text-red-700"}

`}>



{

loadedExample.expectedResult==="SAFE"

?

<CheckCircle size={18}/>

:

<AlertTriangle size={18}/>

}



Example expected:

<b>

{loadedExample.expectedResult}

</b>



</div>

)}




<button


disabled={loading}


onClick={handleAnalyze}


className="w-full bg-indigo-600 text-white p-4 rounded-lg font-semibold"


>


<Search size={20} className="inline mr-2"/>


{

loading
?
"Analysing..."
:
"Analyze with AI"

}


</button>



</div>


</div>






{/* EXAMPLES */}


<div className="grid md:grid-cols-2 gap-6">



<div className="bg-green-50 p-6 rounded-xl">


<h2 className="font-bold text-xl text-green-900 mb-4">

Safe Examples

</h2>


{

safeExamples
.filter(e=>e.type===activeTab)
.map(example=>(


<button

key={example.id}

onClick={()=>handleExampleClick(example)}

className="block w-full text-left bg-white p-4 rounded-lg mb-3"

>


<b>{example.label}</b>


<p className="text-sm">

{example.description}

</p>


<p className="text-xs mt-2 break-all">

{example.content}

</p>


</button>


))

}


</div>







<div className="bg-red-50 p-6 rounded-xl">


<h2 className="font-bold text-xl text-red-900 mb-4">

Malicious Examples

</h2>



{

maliciousExamples
.filter(e=>e.type===activeTab)
.map(example=>(


<button

key={example.id}

onClick={()=>handleExampleClick(example)}

className="block w-full text-left bg-white p-4 rounded-lg mb-3"

>


<b>{example.label}</b>


<p className="text-sm">

{example.description}

</p>


<p className="text-xs mt-2 break-all">

{example.content}

</p>



</button>


))


}



</div>


</div>






<div className="bg-amber-50 p-6 rounded-xl">


<div className="flex gap-3">


<Shield/>


<div>


<h3 className="font-bold">

Keep yourself safe

</h3>


<ul>

<li>• Do not click unknown links</li>

<li>• Never share OTP/password</li>

<li>• Check website spelling</li>

</ul>


</div>


</div>


</div>



</div>


);

}