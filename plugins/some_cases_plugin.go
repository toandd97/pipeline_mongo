
package main
import (
    "os"
    "github.com/gofrs/uuid"
    "github.com/rwynn/monstache/v6/monstachemap"
    "go.mongodb.org/mongo-driver/bson/primitive"
)

// Map is a mapper plugin function that takes an input document and returns a modified document.
// It converts all string values in the input document to uppercase, and adds a new field "profile_event_relations"
// with a value of {"name": "profile"}. It also extracts the "profile_id" field and converts it to a string,
// which is used as the document ID and routing value.
func Map(input *monstachemap.MapperPluginInput) (output *monstachemap.MapperPluginOutput, err error) {
    indexMapping, exists := os.LookupEnv("INDEX_MAPPING")
    if !exists || indexMapping == "" {
        indexMapping = "mobio-profiling-v16_3"
        // return nil, fmt.Errorf("INDEX_MAPPING environment variable is not set")
    }
    // Create a copy of the document
    doc := input.Document
    outputDoc := make(map[string]interface{})
    var idOutput string

    // Iterate through the document
    for k, v := range doc {
        // Check if value is not nil and not empty
        if v == nil || v == "" {
            continue
        }
        outputDoc[k] = v
    }

    // Set profile_event_relations
    outputDoc["profile_event_relations"] = map[string]interface{}{
        "name": "profile",
    }
    
    if profileID, ok := doc["parent_id"].(primitive.Binary); ok && (profileID.Subtype == 3 || profileID.Subtype == 4) {
        if uid, err := uuid.FromBytes(profileID.Data); err == nil {
            idOutput = uid.String()
        }
    }

    // Set the modified document to the output
    output = &monstachemap.MapperPluginOutput{
        Document: outputDoc,
        ID:       idOutput,
        Index:    indexMapping,
        Routing:  idOutput,
    }
    return
}
