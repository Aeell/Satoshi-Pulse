import { Card, Title, Text, TextInput, Button } from '@tremor/react'

const Settings = () => {
  return (
    <Card>
      <Title>Settings</Title>
      <div className="mt-4 space-y-4">
        <div>
          <Text>API URL</Text>
          <TextInput placeholder="http://localhost:8000" />
        </div>
        <div>
          <Text>Binance API Key</Text>
          <TextInput placeholder="Enter API key" />
        </div>
        <div>
          <Text>Binance Secret</Text>
          <TextInput placeholder="Enter secret" type="password" />
        </div>
        <Button>Save Settings</Button>
      </div>
    </Card>
  )
}

export default Settings