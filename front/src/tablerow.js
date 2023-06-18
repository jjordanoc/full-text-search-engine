import React from "react";

const TableRow = ({rowData}) =>{
    return(
        <tr>
            {rowData.map((cellData,index) =>(
                <td key={index}>{cellData}</td>
            ))}
        </tr>
    );
}

export default TableRow;