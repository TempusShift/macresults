const fs = require('fs');
const { files } = require('./rookie_most_improved_config.json');
const htmlparser2 = require('htmlparser2');
const aliases = require('../aliases.json')

const results = [];
const promises = [];

files
  // .slice(files.length - 1)
  .forEach(filename => {
    promises.push(
      new Promise((resolve, reject) => {
        fs.readFile(filename, 'utf8', function (err, data) {
          if (err) reject(err);
          console.log('OK: ' + filename);
          resolve(data);
        });
      })
    );
  });

const driverYears = {};

const checkAlias = (name) => {
  if (aliases[name.toLowerCase()]) {
    return aliases[name.toLowerCase()]
  }
  return name
}

Promise.all(promises).then(filesData => {
  filesData.forEach((fileData, fileIndex) => {
    const dom = htmlparser2.parseDocument(fileData);
    const driverRows = htmlparser2.DomUtils.getElementsByTagName(
      'tr',
      dom
    ).slice(1);
    const drivers = {};
    let scoredEventCount = 0;
    driverRows.forEach((driverRow, driverIndex) => {
      const driverCells = htmlparser2.DomUtils.getElementsByTagName(
        'td',
        driverRow
      );
      const eventCount = parseInt(htmlparser2.DomUtils.getText(driverCells[3]));
      const driverName = checkAlias(htmlparser2.DomUtils.getText(driverCells[1]));
      if (!driverYears[driverName]) {
        driverYears[driverName] = {present:[],complete:[]};
      }
      driverYears[driverName].present.push(files[fileIndex])
      drivers[driverName] = {
        driverName,
        place: driverIndex + 1,
        eventCount,
        completeSeason: eventCount >= scoredEventCount
      };
      if (eventCount >= scoredEventCount) { // || driverName === 'Andrew Deck') {
        scoredEventCount = eventCount;
        driverYears[driverName].complete.push(files[fileIndex]);
      }
    });
    results.push(drivers);
  });
  const newDrivers = [];
  let improvedDrivers = [];
  Object.keys(driverYears).forEach(driverName => {
    const {present, complete} = driverYears[driverName];
    if (present.length === 1 && present[0] === files[files.length - 1]) {
      newDrivers.push(driverName);
    }
    if (
      complete.includes(files[files.length - 1]) &&
      complete.includes(files[files.length - 2])
    ) {
      improvedDrivers.push(driverName);
    }
  });
  const currentYear = results[results.length - 1];

  const rookieOfTheYear = newDrivers
    .sort((a, b) => {
      return currentYear[a].place > currentYear[b].place ? 1 : -1;
    })
    .map(driver => `${driver} - ${currentYear[driver].place} -- ${currentYear[driver].completeSeason}`);

  const previousYear = results[results.length - 2];
  improvedDrivers = improvedDrivers
    .map(driver => {
      const currentPlace = currentYear[driver].place;
      const previousPlace = previousYear[driver].place;
      return {
        driver,
        currentPlace,
        previousPlace,
        difference: previousPlace - currentPlace,
      };
    })
    .sort((a, b) => (a.difference < b.difference ? 1 : -1));
    console.log(`new drivers: (${rookieOfTheYear.length})\nName - Place -- Complete Season`,rookieOfTheYear)
    console.log(`doty place changes: (${improvedDrivers.length})`,improvedDrivers)
});
