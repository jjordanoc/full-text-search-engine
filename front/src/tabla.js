import React from "react";
import TableRow from './tablerow'
import './tabla.css'
const Tabla = (props) =>{
    return(
        <table>
            <thead>
                <tr>
                    {props.headers.map((header,index) =>(
                        <th key={index}>{header}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {props.data.map((rowData,index) =>(
                    <TableRow key={index} rowData={rowData}/>
                ))}
            </tbody>
        </table>
    )
}
export default Tabla;