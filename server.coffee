CLIENT_ID = "223831830375-9v1i6j0vtmtf4kgtvmq9i98hpsh3and4.apps.googleusercontent.com"
CLIENT_SECRET = "MOQuh1PZHAlzAEcJDqj1_oqp"
REDIRECT_URL = ""
  
google = require("googleapis")
OAuth2 = google.auth.OAuth2
oauth2Client = new OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URL)

# generate a url that asks permissions for Google+ and Google Calendar scopes
scopes = [
  "https://www.googleapis.com/auth/gmail.readonly"
  "profile"
  "email"
]

# url = oauth2Client.generateAuthUrl(
#   access_type: "offline" # 'online' (default) or 'offline' (gets refresh_token)
#   scope: scopes # If you only need one scope you can pass it as string
# )

request = require("request")
googleIdToken = require("google-id-token")

# kid = the key id specified in the token
getGoogleCerts = (kid, callback) ->
  request
    uri: "https://www.googleapis.com/oauth2/v1/certs"
  , (err, response, body) ->
    if err and response.statusCode isnt 200
      err = err or "error while retrieving the google certs"
      console.log err
      callback err, {}
    else
      keys = JSON.parse(body)
      callback null, keys[kid]
    return

  return

parser = new googleIdToken(getKeys: getGoogleCerts)

moment = require("moment")
express = require("express")
app = express()
app.get "/kickoff", (req, res) ->
  code = req.query.code
  console.log code
  oauth2Client.getToken code, (err, tokens) ->
    console.log err,tokens
    if not tokens
      res.status(404).end()
      return
    res.send({status:"OK"});
    tokens["_class"] = "OAuth2Credentials"
    tokens["_module"] = "oauth2client.client"
    # storage["access_token"] = jsonAuth["access_token"]
    tokens["client_id"] = CLIENT_ID
    tokens["client_secret"] = CLIENT_SECRET
    tokens["invalid"] = false
    tokens["revoke_uri"] = "https://accounts.google.com/o/oauth2/revoke"
    tokens["token_expiry"] = moment().add(3600,'s').format()
    tokens["token_response"] = 
      access_token: tokens.access_token
      expires_in: tokens.expires_in
      id_token: tokens.id_token
      token_type: tokens.token_type
    tokens["token_uri"] = "https://accounts.google.com/o/oauth2/token"
    tokens["user_agent"] = null
    
    parser.decode tokens.id_token, (err, token) ->
      if err
        return
      tokens.id_token = token.data
      tokenJSONStr = JSON.stringify(tokens)
      console.log tokenJSONStr
      # Now tokens contains an access_token and an optional refresh_token. Save them.
      # oauth2Client.setCredentials tokens  unless err
      exec = require('child_process').exec


      fs = require 'fs'


      child = exec("python /root/nodejsPeaps/main.py " +"'"+tokenJSONStr+"'", (error, stdout, stderr) ->
        console.log "stdout: " + stdout
        console.log "stderr: " + stderr
        console.log "exec error: " + error  if error isnt null

        # fs.writeFile "/root/nodejsPeaps/stdout.txt", stdout
        # fs.writeFile "/root/nodejsPeaps/stderr.txt", stderr

        return
      )
      return    
  return

app.listen(process.env.PORT or 80)

