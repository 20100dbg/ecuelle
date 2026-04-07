const { createApp } = Vue
const socket = io();

createApp({
    data: () => ({
      connections: [],
      //{ip:"", port:"", hash:"", salt:""}
      
      queries: [],
      //{query: "", error:"XXXX/false", result:{cols:[], rows:[]}}

      result: 0
    }),

    created() {
      socket.on("connect", () => { console.log('connected'); });
      socket.on("disconnect", () => { console.log('disconnected'); });
      

      socket.on("result", (msg) => {
        this.result = msg.data;
      });

      socket.on("msg", (msg) => {

        console.log(msg);

        if (msg.info) {
        }

        if (msg.query) {
          let q = {'query': msg.query, 'result': ''}
          _queries.values.push(q)
        }

        if (msg.result) {
          let q = _queries.values[_queries.values.length-1];
          q['result'] = msg.result;
          q['error'] = false;
          _queries.values[_queries.values.length-1] = q;
        }

        if (msg.error) {
          let q = _queries.values[_queries.values.length-1];
          q['result'] = false;
          q['error'] = msg.error;
          _queries.values[_queries.values.length-1] = q;
        }

      });
    },

    methods: {

      onrequest() {
        socket.emit('request', {});
      }

    }

}).mount("#app");
