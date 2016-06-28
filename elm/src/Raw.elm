module Raw exposing (..)

import Date
import Array

import Http
import Json.Decode as Decode exposing (Decoder, (:=))
import DecodeExtra exposing (pure, apply)
import Json.Encode as Encode


toBody: a -> (a -> Encode.Value) -> Http.Body
toBody model modelEncoder = Http.string (Encode.encode 0 (modelEncoder model))


--


type alias Column =
    { id: Int
    , name: String
    , full_name: String
    , description: String
    , data_type: String
    , data_table_group: String
    , table_order: Int
    }


columnDecoder: Decoder Column
columnDecoder =
    Decode.object7 Column
    ("id" := Decode.int)
    ("name" := Decode.string)
    ("full_name" := Decode.string)
    ("description" := Decode.string)
    ("data_type" := Decode.string)
    ("data_table_group" := Decode.string)
    ("table_order" := Decode.int)


columnEncoder: Column -> Encode.Value
columnEncoder column =
    Encode.object
    [ ("id", Encode.int column.id)
    , ("name", Encode.string column.name)
    , ("full_name", Encode.string column.full_name)
    , ("description", Encode.string column.description)
    , ("data_type", Encode.string column.data_type)
    , ("data_table_group", Encode.string column.data_table_group)
    , ("table_order", Encode.int column.table_order)]


columnToBody: Column -> Http.Body
columnToBody column = toBody column columnEncoder


columnEx: Column
columnEx =
    { id=0
    , data_table_group= "price"
    , name="A"
    , full_name="B"
    , description="Foo"
    , data_type="bigint"
    , table_order=2
    }


--


type alias DataTableGroup =
    { id: Int
    , name: String
    , full_name: String
    , project: String
    , description: String
    , url: String
    , columns: Array.Array Column
    , number_of_files: Int
    , number_of_columns: Int
    }


datatablegroupDecoder: Decoder DataTableGroup
datatablegroupDecoder =
    pure DataTableGroup
    `apply` ("id" := Decode.int)
    `apply` ("name" := Decode.string)
    `apply` ("full_name" := Decode.string)
    `apply` ("project" := Decode.string)
    `apply` ("description" := Decode.string)
    `apply` ("url" := Decode.string)
    `apply` ("columns":= Decode.array columnDecoder)
    `apply` ("number_of_files" := Decode.int)
    `apply` ("number_of_columns" := Decode.int)


datatablegroupEncoder: DataTableGroup -> Encode.Value
datatablegroupEncoder datatablegroup =
    Encode.object
    [ ("id", Encode.int datatablegroup.id)
    , ("name", Encode.string datatablegroup.name)
    , ("full_name", Encode.string datatablegroup.full_name)
    , ("project", Encode.string datatablegroup.project)
    , ("url", Encode.string datatablegroup.url)
    , ("columns", Encode.array (Array.map columnEncoder datatablegroup.columns))
    , ("number_of_files", Encode.int datatablegroup.number_of_files)
    , ("number_of_columns", Encode.int datatablegroup.number_of_columns) ]


datatablegroupBody: DataTableGroup -> Http.Body
datatablegroupBody datatablegroup = toBody datatablegroup datatablegroupEncoder


datatablegroupEx =
    { id=0
    , name="DT"
    , full_name="DTG"
    , project="Luxe Demo"
    , url="d"
    , columns= Array.fromList [columnEx]
    , number_of_files= 10
    , number_of_columns= 1
    }


--


type alias Parameter =
    { id: Int
    , name: String
    , label: String
    , data_type: String
    , description: String
    , value: String
    , html_input_type: String
    , value_list: Maybe (Array.Array String)
    , value_range: Maybe (Array.Array String)
    }


parameterDecoder: Decoder Parameter
parameterDecoder =
    pure Parameter
    `apply` ("id" := Decode.int)
    `apply` ("name" := Decode.string)
    `apply` ("label" := Decode.string)
    `apply` ("data_type" := Decode.string)
    `apply` ("description" := Decode.string)
    `apply` ("value" := Decode.string)
    `apply` ("html_input_type" := Decode.string)
    `apply` ("value_list" := Decode.maybe
        (Decode.oneOf
            [ Decode.array Decode.string
            , Decode.customDecoder (Decode.array Decode.float) (\xs -> Result.Ok (Array.map toString xs))
            ]))
    `apply` ("value_range" := Decode.maybe
        (Decode.oneOf
            [ Decode.array Decode.string
            , Decode.customDecoder (Decode.array Decode.float) (\xs -> Result.Ok (Array.map toString xs))
            ]))


parameterEncoder: Parameter -> Encode.Value
parameterEncoder parameter =
    let encodeMaybeArray maybe_array =
            case maybe_array of
                Just list -> Encode.array (Array.map Encode.string list)
                Nothing -> Encode.null
    in
    Encode.object
    [ ("id", Encode.int parameter.id)
    , ("label", Encode.string parameter.label)
    , ("data_type", Encode.string parameter.data_type)
    , ("description", Encode.string parameter.description)
    , ("value", Encode.string parameter.value)
    , ("html_input_type", Encode.string parameter.html_input_type)
    , ("value_list", encodeMaybeArray parameter.value_list)
    , ("value_range", encodeMaybeArray parameter.value_range)]


type alias Analysis =
    { id: Int
    , name: String
    , full_name: String
    , date_created: Date.Date
    , last_modified: Date.Date
    , description: String
    , project: String
    , file_type: String
    , parameters: Array.Array Parameter
    }


analysisDecoder: Decoder Analysis
analysisDecoder =
    let dateDecoder = Decode.customDecoder Decode.string Date.fromString
    in
    pure Analysis
    `apply` ("id" := Decode.int)
    `apply` ("name" := Decode.string)
    `apply` ("full_name" := Decode.string)
    `apply` ("date_created" := dateDecoder)
    `apply` ("last_modified" := dateDecoder)
    `apply` ("description" := Decode.string)
    `apply` ("project" := Decode.string)
    `apply` ("file_type" := Decode.string)
    `apply` ("parameters" := Decode.array parameterDecoder)


analysisEncoder: Analysis -> Encode.Value
analysisEncoder { id
                , name
                , full_name
                , date_created
                , last_modified
                , description
                , project
                , file_type
                , parameters} =
    Encode.object
    [ ("id", Encode.int id)
    , ("name", Encode.string name)
    , ("full_name", Encode.string full_name)
--    , ("date_created", Encode.string date_created)
--    , ("last_modified", Encode.string last_modified)
    , ("description", Encode.string description)
    , ("project", Encode.string project)
    , ("file_type", Encode.string file_type)
    , ("parameters", Encode.array (Array.map parameterEncoder parameters))]


type alias RecentActivity =
 { creator: String
 , action: String
 , message: String
 , date_created: Date.Date
 , project: String
 }


recentactivityDecoder: Decoder RecentActivity
recentactivityDecoder =
    let dateDecoder = Decode.customDecoder Decode.string Date.fromString
    in
    pure RecentActivity
    `apply` ("creator" := Decode.string)
    `apply` ("action" := Decode.string)
    `apply` ("message" := Decode.string)
    `apply` ("date_created" := dateDecoder)
    `apply` ("project" := Decode.string)


type alias ProjectIncoming =
    { id: Int
    , url: String
    , group_members: Array.Array String
    , creator: String
    , published: Bool
    , published_on: Maybe Date.Date
    , date_created: Date.Date
    , number_of_datasets: Int
    , data_table_groups: Array.Array DataTableGroup
    , analyses: Array.Array Analysis
    , slug: String
    , description: String
    , name: String
    , comments: Array.Array String
    , recent_activity: Array.Array RecentActivity
    }


projectDecoder: Decoder ProjectIncoming
projectDecoder =
    let dateDecoder = Decode.customDecoder Decode.string Date.fromString
    in
    pure ProjectIncoming
    `apply` ("id" := Decode.int)
    `apply` ("url" := Decode.string)
    `apply` ("group_members" := Decode.array Decode.string)
    `apply` ("creator" := Decode.string)
    `apply` ("published" := Decode.bool)
    `apply` ("published_on" :=
        Decode.customDecoder
            (Decode.maybe Decode.string)
            (\ms -> case ms of
                Just s -> Result.map Just (Date.fromString s)

                Nothing -> Result.Ok Nothing))
    `apply` ("date_created" := dateDecoder)
    `apply` ("number_of_datasets" := Decode.int)
    `apply` ("data_table_groups" := Decode.array datatablegroupDecoder)
    `apply` ("analyses" := Decode.array analysisDecoder)
    `apply` ("slug" := Decode.string)
    `apply` ("description" := Decode.string)
    `apply` ("name" := Decode.string)
    `apply` ("comments" := Decode.array Decode.string)
    `apply` ("recent_activity" := Decode.array recentactivityDecoder)


type alias ProjectOutgoing =
    { id: Int
    , creator: String
    , published: Bool
    , slug: String
    , description: String
    , name: String
    }

projectEncoder: ProjectOutgoing -> Encode.Value
projectEncoder { id
               , creator
               , published
               , slug
               , description
               , name
               } =
    Encode.object
    [ ("id", Encode.int id)
    , ("creator", Encode.string creator)
    , ("published", Encode.bool published)
    , ("slug", Encode.string slug)
    , ("description", Encode.string description)
    , ("name", Encode.string name)]
