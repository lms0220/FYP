import { type ReactNode, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  CalendarDays,
  FolderOpen,
} from "lucide-react";

import {
  getHistory,
  type HistoryItem,
} from "../api";



type DashboardStat = {
  label:string;
  value:number;
  color:string;
  icon:ReactNode;
};



type ActivityItem = {

  id:string;

  type:"sms"|"url";

  classification:"SAFE"|"MALICIOUS";

  content:string;

  confidence:number;

  createdAt:string;

};





const initialStats={

  total:0,

  malicious:0,

  safe:0,

  thisWeek:0,

};






function formatRelativeTime(dateString:string){


  const date = new Date(dateString);

  const diff =
    Date.now()-date.getTime();



  if(diff < 0)
    return "Just now";



  const minutes =
    Math.floor(diff/60000);


  const hours =
    Math.floor(minutes/60);


  const days =
    Math.floor(hours/24);



  if(minutes < 60)
    return `${minutes} minutes ago`;



  if(hours < 24)
    return `${hours} hours ago`;



  return `${days} days ago`;

}









export default function Dashboard(){


const navigate = useNavigate();



const [dashboardStats,setDashboardStats]
=
useState(initialStats);



const [activity,setActivity]
=
useState<ActivityItem[]>([]);



const [username,setUsername]
=
useState("User");



const [loading,setLoading]
=
useState(true);






useEffect(()=>{


const name =
sessionStorage.getItem(
"scamShieldUsername"
);



if(name){

setUsername(name);

}






const loadDashboard = async()=>{


try{


const results:HistoryItem[] =
await getHistory();





const sorted =
[
...results
]
.sort(
(a,b)=>
new Date(b.created_at).getTime()
-
new Date(a.created_at).getTime()
);




const total =
sorted.length;



const malicious =
sorted.filter(
item=>
item.classification !== "SAFE"
).length;




const safe =
sorted.filter(
item=>
item.classification==="SAFE"
).length;






const weekAgo =
new Date(
Date.now()-7*24*60*60*1000
);



const thisWeek =
sorted.filter(
item=>
new Date(item.created_at)>=weekAgo
).length;







const recent =
sorted
.slice(0,4)
.map(item=>({

id:item.result_id,

type:item.type,

classification:
item.classification==="SAFE"
?
"SAFE"
:
"MALICIOUS",

content:item.content,

confidence:
Number(item.confidence_score),

createdAt:item.created_at,


}));






setDashboardStats({

total,

malicious,

safe,

thisWeek,

});



setActivity(
recent as ActivityItem[]
);




}
catch(error){

console.error(
"Dashboard error:",
error
);


}

finally{


setLoading(false);


}


};




loadDashboard();



},[]);







const stats:DashboardStat[]=[


{

label:"Total Scans",

value:dashboardStats.total,

color:
"bg-blue-100 text-blue-700",

icon:
<FolderOpen className="w-6 h-6 text-blue-600"/>

},



{

label:"Threats Detected",

value:dashboardStats.malicious,

color:
"bg-red-100 text-red-700",

icon:
<AlertTriangle className="w-6 h-6 text-red-600"/>

},



{

label:"Safe Items",

value:dashboardStats.safe,

color:
"bg-green-100 text-green-700",

icon:
<CheckCircle className="w-6 h-6 text-green-600"/>

},



{

label:"This Week",

value:dashboardStats.thisWeek,

color:
"bg-indigo-100 text-indigo-700",

icon:
<CalendarDays className="w-6 h-6 text-indigo-600"/>

}


];









if(loading){


return(

<div className="p-6 text-center">

Loading dashboard...

</div>

);


}










return(


<div className="space-y-8 p-6">





<div className="
bg-gradient-to-r
from-indigo-600
to-blue-600
rounded-2xl
shadow-lg
p-8
text-white
">


<h1 className="text-4xl font-bold">

Welcome back, {username}

</h1>


<p className="mt-3 text-indigo-100">

AI-powered phishing protection

</p>



<div className="mt-6 flex gap-3">


<button

onClick={()=>
navigate("/app/submit")
}

className="
bg-white
text-indigo-700
px-6
py-3
rounded-xl
font-semibold
"

>

Submit Analysis

</button>




<button

onClick={()=>
navigate("/app/history")
}

className="
border
border-white/30
px-6
py-3
rounded-xl
"

>

History

</button>


</div>



</div>









<div className="
grid
grid-cols-1
md:grid-cols-2
xl:grid-cols-4
gap-6
">


{
stats.map(stat=>(


<div

key={stat.label}

className="
bg-white
rounded-3xl
shadow
p-6
flex
justify-between
"

>


<div>

<p className="text-gray-500">

{stat.label}

</p>


<p className="
text-4xl
font-bold
mt-3
">

{stat.value}

</p>


</div>



<div className={`
w-14
h-14
rounded-2xl
flex
items-center
justify-center
${stat.color}
`}>

{stat.icon}


</div>



</div>


))

}


</div>









<div className="
bg-white
rounded-3xl
shadow
p-6
">


<div className="
flex
justify-between
mb-6
">


<h2 className="text-2xl font-bold">

Recent Activity

</h2>


<button

onClick={()=>
navigate("/app/history")
}

className="
text-indigo-600
flex
gap-2
"

>

View All

<ArrowRight size={18}/>

</button>


</div>







{
activity.length===0

?

<p className="text-gray-500">

No analysis history yet.

</p>


:

activity.map(item=>(


<button
key={item.id}
onClick={() =>
  navigate(
    `/app/results/${item.id}`,
    {
      state: {
        result: {
          type: item.type,
          prediction: item.classification,
          score: item.confidence,
          flags: []
        },
        content: item.content
      }
    }
  )
}
className="
w-full
text-left
bg-gray-50
rounded-3xl
p-5
hover:shadow
overflow-hidden
"
>

<div className="flex justify-between items-center gap-4">

  {/* Content box */}
  <div className="flex-1 min-w-0">

    <p className="
    font-semibold
    truncate
    max-w-full
    ">
      {item.content}
    </p>

    <p className="text-sm text-gray-500">
      {item.type.toUpperCase()}
      {" • "}
      {formatRelativeTime(item.createdAt)}
    </p>

  </div>


  {/* Confidence box */}
  <div className="
  flex-shrink-0
  w-20
  text-right
  ">

    <p className="text-2xl font-bold">
      {item.confidence}%
    </p>

  </div>


</div>

</button>


))


}





</div>






<div className="
bg-amber-50
border
border-amber-200
rounded-3xl
p-6
">


<h3 className="
font-bold
text-xl
text-amber-900
">

Stay Safe Online

</h3>



<ul className="
mt-3
space-y-2
text-amber-900
">


<li>
• Do not click unknown links
</li>


<li>
• Verify sender identity
</li>


<li>
• Enable two-factor authentication
</li>


</ul>


</div>




</div>


);


}