import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  History as HistoryIcon,
  AlertTriangle,
  CheckCircle,
  Search,
  Download,
  Trash2,
} from "lucide-react";

import {
  getHistory,
  deleteHistory,
  type HistoryItem,
} from "../api";


type FilterType = "all" | "malicious" | "safe";


export default function History() {

  const navigate = useNavigate();


  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<HistoryItem[]>([]);

  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");

  const [selectedItems, setSelectedItems] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");



  useEffect(() => {

    loadHistory();

  }, []);



  const loadHistory = async () => {

    try {

      setLoading(true);

      const data = await getHistory();

      setHistory(data);

    } catch(error) {

      console.error(error);

      setError(
        error instanceof Error
        ? error.message
        : "Failed to load history"
      );

    } finally {

      setLoading(false);

    }

  };




  useEffect(() => {


    const result = history.filter((item)=>{


      const searchMatch =
        item.content
        .toLowerCase()
        .includes(searchTerm.toLowerCase());



      const filterMatch =
        filter === "all"
        ||
        (
          filter === "safe"
          &&
          item.classification === "SAFE"
        )
        ||
        (
          filter === "malicious"
          &&
          item.classification !== "SAFE"
        );



      return searchMatch && filterMatch;


    });


    setFilteredHistory(result);


  },[
    history,
    searchTerm,
    filter
  ]);






  const toggleSelect = (id:string)=>{


    setSelectedItems(prev=>

      prev.includes(id)

      ?

      prev.filter(item=>item!==id)

      :

      [
        ...prev,
        id
      ]

    );


  };




  const toggleSelectAll = ()=>{


    if(
      selectedItems.length === filteredHistory.length
      &&
      filteredHistory.length > 0
    ){

      setSelectedItems([]);

    }

    else{

      setSelectedItems(
        filteredHistory.map(
          item=>item.result_id
        )
      );

    }


  };





  const deleteSelected = async()=>{


    if(selectedItems.length===0)
      return;



    const confirm =
      window.confirm(
        "Delete selected records?"
      );



    if(!confirm)
      return;



    try{


      await deleteHistory(selectedItems);



      setHistory(prev=>

        prev.filter(
          item=>
          !selectedItems.includes(
            item.result_id
          )
        )

      );



      setSelectedItems([]);



    }
    catch(error){

      console.error(error);

      alert("Delete failed");

    }


  };








  const exportCSV = ()=>{


    if(filteredHistory.length===0){

      alert("No data available");

      return;

    }



    const headers=[
      "Type",
      "Content",
      "Result",
      "Confidence",
      "Date",
      "Status"
    ];



    const rows =
      filteredHistory.map(item=>[

        item.type,

        `"${item.content.replaceAll('"','""')}"`,

        item.classification,

        `${item.confidence_score}%`,

        new Date(
          item.created_at
        ).toLocaleString(),

        item.status

      ]);




    const csv=[
      headers.join(","),

      ...rows.map(
        row=>row.join(",")
      )

    ].join("\n");



    const blob =
      new Blob(
        [csv],
        {
          type:"text/csv"
        }
      );



    const url =
      URL.createObjectURL(blob);



    const link =
      document.createElement("a");



    link.href=url;

    link.download=
      `scam-history-${Date.now()}.csv`;



    link.click();



    URL.revokeObjectURL(url);


  };








  const stats={

    total:history.length,

    malicious:
      history.filter(
        item=>
        item.classification!=="SAFE"
      ).length,


    safe:
      history.filter(
        item=>
        item.classification==="SAFE"
      ).length

  };






  if(loading){

    return(
      <div className="text-center py-12">
        Loading history...
      </div>
    );

  }




  if(error){

    return(
      <div className="text-center py-12 text-red-600">
        {error}
      </div>
    );

  }







  return (

<div className="space-y-6">



<div className="bg-white rounded-xl shadow p-6">


<div className="flex justify-between items-center mb-6">


<div className="flex items-center gap-3">

<HistoryIcon className="text-indigo-600" size={32}/>


<div>

<h1 className="text-2xl font-bold">
Analysis History
</h1>


<p className="text-gray-600">
View previous scam detection results
</p>


</div>


</div>



<button

onClick={exportCSV}

className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg"

>

<Download size={18}/>

Export

</button>


</div>





<div className="grid md:grid-cols-3 gap-4">


<div className="bg-blue-50 p-4 rounded-lg">

<p>Total Scans</p>

<h2 className="text-3xl font-bold">
{stats.total}
</h2>

</div>




<div className="bg-red-50 p-4 rounded-lg">

<p>Threats</p>

<h2 className="text-3xl font-bold">
{stats.malicious}
</h2>

</div>




<div className="bg-green-50 p-4 rounded-lg">

<p>Safe</p>

<h2 className="text-3xl font-bold">
{stats.safe}
</h2>

</div>


</div>


</div>






<div className="bg-white rounded-xl shadow p-6">


<div className="flex gap-4">


<div className="flex-1 relative">


<Search
className="absolute left-3 top-3 text-gray-400"
/>


<input

value={searchTerm}

onChange={
e=>setSearchTerm(e.target.value)
}

placeholder="Search history..."

className="w-full pl-10 border rounded-lg p-2"

/>


</div>




<button
onClick={()=>setFilter("all")}
className="px-4 rounded-lg bg-gray-100"
>
All
</button>


<button
onClick={()=>setFilter("malicious")}
className="px-4 rounded-lg bg-red-100"
>
Malicious
</button>


<button
onClick={()=>setFilter("safe")}
className="px-4 rounded-lg bg-green-100"
>
Safe
</button>


</div>





{
selectedItems.length>0 &&

<button

onClick={deleteSelected}

className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg flex gap-2"

>

<Trash2 size={18}/>

Delete Selected

</button>

}



</div>









<div className="bg-white rounded-xl shadow overflow-hidden">


<table className="w-full">


<thead className="bg-gray-100">

<tr>

<th className="p-4">

<input

type="checkbox"

checked={
selectedItems.length===filteredHistory.length
&&
filteredHistory.length>0
}

onChange={toggleSelectAll}

/>

</th>


<th className="p-4 text-left">
Type
</th>


<th className="p-4 text-left">
Content
</th>


<th className="p-4 text-left">
Result
</th>


<th className="p-4 text-left">
Confidence
</th>


<th className="p-4 text-left">
Date
</th>


</tr>


</thead>




<tbody>


{
filteredHistory.map(item=>(


<tr

key={item.result_id}

className="hover:bg-gray-50 cursor-pointer"

onClick={()=>


navigate(
`/app/results/${item.result_id}`,
{

state:{

result:{

type:item.type,

prediction:item.classification,

score:item.confidence_score,

flags:[]

},

content:item.content

}

}

)


}


>


<td className="p-4">


<input

type="checkbox"

checked={
selectedItems.includes(
item.result_id
)
}

onClick={
e=>e.stopPropagation()
}

onChange={()=>toggleSelect(item.result_id)}

/>


</td>




<td className="p-4">

{item.type.toUpperCase()}

</td>




<td className="p-4 max-w-md truncate">

{item.content}

</td>




<td className="p-4">


{
item.classification==="SAFE"

?

<CheckCircle
className="text-green-600"
/>

:

<AlertTriangle
className="text-red-600"
/>

}


{item.classification}


</td>




<td className="p-4">

{item.confidence_score}%

</td>




<td className="p-4">

{
new Date(
item.created_at
).toLocaleString()
}

</td>



</tr>


))


}



</tbody>



</table>



{
filteredHistory.length===0 &&

<div className="text-center p-8 text-gray-500">

No history found

</div>

}



</div>




</div>


  );

}