/* Timeframe, version 0.2
 * (c) 2008 Stephen Celis
 *
 * Freely distributable under the terms of an MIT-style license. 
 * ------------------------------------------------------------- */

if (typeof Prototype == 'undefined' || parseFloat(Prototype.Version.substring(0, 3)) < 1.6)
  throw 'Timeframe requires Prototype version 1.6 or greater.';

Array.prototype.contains = function(obj) {
    var i = this.length;
    while (i--) {
        if (this[i] == obj) {
            return true;
        }
    }
    return false;
}

if(!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(needle) {
        for(var i = 0; i < this.length; i++) {
            if(this[i] === needle) {
                return i;
            }
        }
        return -1;
    };
}

// Checks for localized Datejs before defaulting to 'en-US'
var Locale = $H({
  format:     (typeof Date.CultureInfo == 'undefined' ? '%b %d, %Y' : Date.CultureInfo.formatPatterns.shortDate),
  monthNames: (typeof Date.CultureInfo == 'undefined' ? $w('Janvier Février Mars Avril Mai Juin Juillet Août Septembre Octobre Novembre Décembre') : Date.CultureInfo.monthNames),
  dayNames:   (typeof Date.CultureInfo == 'undefined' ? $w('Dimanche Lundi Mardi Mercredi Jeudi Vendredi Samedi') : Date.CultureInfo.dayNames),
  weekOffset: (typeof Date.CultureInfo == 'undefined' ? 0 : Date.CultureInfo.firstDayOfWeek)
});

var days = $H({
  en: $w('Sunday Monday Tuesday Wednesday Thursday Friday Saturday'),
  fr: $w('Dimanche Lundi Mardi Mercredi Jeudi Vendredi Samedi'),
  it: $w('Domenica Lunedì Martedì Mercoledì Giovedì Venerdì Sabato'),
  de: $w('Sonntag Montag Dienstag Mittwoch Donnerstag Freitag Samstag'),
  nl: $w('Zondag Maandag Dinsdag Woensdag Donderdag Vrijdag Zaterdag')
});

var months = $H({
  en: $w('January February March April May June July August September October November December'),
  fr: $w('Janvier Février Mars Avril Mai Juin Juillet Août Septembre Octobre Novembre Décembre'),
  it: $w('Gennaio Febbraio Marzo Aprile Maggio Giugno Luglio Agosto Settembre Ottobre Novembre Dicembre'),
  de: $w('Januar Februar März April Mai Juni Juli August September Oktober November Dezember'),
  nl: $w('Januari Februari Maart April Mei Juni Juli Augustus September Oktober November December')
});

var Timeframes = [];
var Rented = new Hash();

var GiteMultiTimeframe = Class.create({
  Version: '0.2',

  initialize: function(element, options) {
    Timeframes.push(this);

    this.element = $(element);
    this.element.addClassName('timeframe_calendar');
    this.element.addClassName('multicalendar');
    this.options = $H({ months: 1 }).merge(options || {});
    this.language     = this.options.get('language');
    this.weekdayNames = days.get(this.language);
    this.monthNames   = months.get(this.language);
    this.format       = this.options.get('format')     || Locale.get('format');
    this.weekOffset   = this.options.get('weekOffset') || Locale.get('weekOffset');
    this.hebsPks      = this.options.get('hebsPks');
    this.hebsNames    = this.options.get('hebsNames');
    this.maxRange = 99999;
    this.months = 1;
    this.daysNumber = 35;

    this.buttons = $H({
      previous: $H({ label: '&nbsp;', element: $(this.options.get('previousButton')) }),
      today:    $H({ label: '&nbsp;', element: $(this.options.get('todayButton')) }),
      next:     $H({ label: '&nbsp;', element: $(this.options.get('nextButton')) })
    });
    //this.fields = $H({ start: $(this.options.get('startField')), end: $(this.options.get('endField')) });

    this.date = new Date();
    this.range = $H({});
    this._buildButtons()._buildFields();
    this.earliest = Date.parseToObject(this.options.get('earliest'));
    this.latest   = Date.parseToObject(this.options.get('latest'));

    this.register().populate().refreshRange(true);
    this.element.down('div#' + this.element.id + '_container').setOpacity(1);
  },

  // Scaffolding

  createCalendarsHeader: function() {
    var calendar = new Element('table', {
      id: this.element.id + '_calendar_header', border: 0, cellspacing: 0, cellpadding: 5
    });
    calendar.insert(new Element('caption'));
    var caption = calendar.select('caption').first();

    var head = new Element('thead');
    var row  = new Element('tr');
    var iterator = new Date(this.date);
    var displayedMonths;
    if (iterator.getDate() == 1) displayedMonths = 0;
    else displayedMonths = 1;

    this.daysNumber.times(function(dayNum) {
      var weekday = this.weekdayNames[iterator.getDay()];
      var cell = new Element('th', { scope: 'col', abbr: weekday }).update(weekday.substring(0,1));
      if (iterator.getDate() == 1) {
          cell.addClassName('newmonth');
          displayedMonths += 1;
      }
      if (iterator.neutral().toString() === new Date().neutral().toString()) cell.addClassName('today');
      row.insert(cell);
      iterator.setDate(iterator.getDate() + 1);
    }.bind(this));
    head.insert(row);

    var refDate = new Date(this.date);
    refDate.setDate(1);
    var captionStr = '';
    displayedMonths.times(function(month) {
        if (captionStr != '') captionStr += '&nbsp; <strong><font color="Red">|</font></strong> &nbsp;';
        var monthCaption = this.monthNames[refDate.getMonth()] + ' ' + refDate.getFullYear();
        captionStr += monthCaption;
        refDate.setMonth(refDate.getMonth() + 1);
    }.bind(this));
    caption.update(captionStr);

    var row2  = new Element('tr');
    iterator = new Date(this.date);
    this.daysNumber.times(function(dayNum) {
      day = iterator.getDate();
      var cell = new Element('th', { scope: 'col', abbr: day, 'class': '' }).update(day);
      if (iterator.getDate() == 1) cell.addClassName('newmonth');
      if (iterator.neutral().toString() === new Date().neutral().toString()) cell.addClassName('today');
      row2.insert(cell);
      iterator.setDate(iterator.getDate() + 1);
    }.bind(this));
    head.insert(row2);

    calendar.insert(head);
    this.element.down('div#' + this.element.id + '_container').insert(calendar);

    this.calendarHeader = calendar;
    return this;
  },

  createCalendar: function(index) {
    var hebPk = this.hebsPks[index];
    var hebName = this.hebsNames[index];
    var calendar = new Element('table', {
      id: this.element.id + '_calendar_' + hebPk, border: 1, cellspacing: 0, cellpadding: 5
    });
    var body = new Element('tbody');

    var title = new Element('div');
    title.addClassName('gitename');
    if (this.hebsPks.length > 1) title.update('┌ ' + hebName);
    this.element.down('div#' + this.element.id + '_container').insert(title);
    this.titles.push(title);

    var row = new Element('tr');
    var iterator = new Date(this.date);
    this.daysNumber.times(function(dayNum) {
        var day = new Element('td');
        day.date = new Date(iterator);
        day.hebPk = hebPk;
        day.writeAttribute('class', '');

        if (day.hasClassName('active')) day.removeClassName('active');
        if (day.hasClassName('inactive')) day.removeClassName('inactive');
        if (day.hasClassName('unselectable')) day.removeClassName('unselectable');
        if (day.hasClassName('selectable')) day.removeClassName('selectable');
        if (day.hasClassName('today')) day.removeClassName('today');
        if (day.hasClassName('post')) day.removeClassName('post');
        if (day.hasClassName('pre')) day.removeClassName('pre');
        if (day.hasClassName('beyond')) day.removeClassName('beyond');
        if (day.hasClassName('indisp')) day.removeClassName('indisp');
        day.addClassName('active');

        if ((this.earliest && day.date < this.earliest) || (this.latest && day.date > this.latest))
          day.addClassName('unselectable');
        else
          day.addClassName('selectable');
        if (iterator.toString() === new Date().neutral().toString()) day.addClassName('today');  

        day.baseClass = day.readAttribute('class');
        row.insert(day);
        iterator.setDate(iterator.getDate() + 1);
    }.bind(this));

    body.insert(row);
    calendar.insert(body);

    this.element.down('div#' + this.element.id + '_container').insert(calendar);
    this.calendars.push(calendar);
    return this;
  },

  destroyCalendar: function() {
    this.calendarHeader.remove();
    this.titles.each(function(title) { title.remove(); }.bind(this));
    this.calendars.each(function(calendar) { calendar.remove(); }.bind(this));
    return this;
  },

  populate: function() {
    this.calendars = [];
    this.titles = [];
    if (!this.element.down('div#' + this.element.id + '_container'))
        this.element.insert(new Element('div', { id: this.element.id + '_container' }));
    this.element.down('div#' + this.element.id + '_container').setOpacity(0.4);

    this.createCalendarsHeader();
    this.hebsPks.length.times(function(index) { this.createCalendar(index); }.bind(this));
    return this;
  },

  _buildButtons: function() {
    var buttonList = new Element('div', { id: this.element.id + '_menu', className: 'timeframe_menu' });
    this.counter = 1;
    this.buttons.each(function(pair) { 
      if (pair.value.get('element')) 
        pair.value.get('element').addClassName('timeframe_button').addClassName(pair.key); 
      else { 
        var item = new Element('span', { id: 'btn_' + pair.key + '_public'}); 
        var button = new Element('a', { id: 'a_' + pair.key, className: 'timeframe_button ' + pair.key, href: '#', onclick: 'return false;' }).update(pair.value.get('label')); 
        button.onclick = function() { return false; }; 
        switch(this.counter) { 
          case 1: this.buttonPrevious = button;
          case 2: this.buttonToday = button;
          case 3: this.buttonNext = button;
        }
        this.counter += 1;
        pair.value.set('element', button); 
        item.insert(button); 
        buttonList.insert(item); 
      } 
    }.bind(this));
    if (buttonList.childNodes.length > 0) this.element.insert({ top: buttonList });
    this.clearButton = new Element('span', { className: 'clear' }).update(new Element('span').update('X'));
    return this;
  },

  _buildFields: function() {
    var fieldset = new Element('div', { id: this.element.id + '_fields', className: 'timeframe_fields' });
    /*this.fields.each(function(pair) {
      if (pair.value)
        pair.value.addClassName('timeframe_field').addClassName(pair.key);
      else {
        var container = new Element('div', { id: pair.key + this.element.id + '_field_container' });
        this.fields.set(pair.key, new Element('input', { id: this.element.id + '_' + pair.key + 'field', name: pair.key + 'field', type: 'text', value: '' }));
        container.insert(new Element('label', { 'for': pair.key + 'field' }).update(pair.key));
        container.insert(this.fields.get(pair.key));
        fieldset.insert(container);
      }
    }.bind(this));*/
    if (fieldset.childNodes.length > 0) this.element.insert(fieldset);
    this.parseField('start').refreshField('start').parseField('end').refreshField('end').initDate = new Date(this.date);
    return this;
  },

  // Event registration

  selectPreviousMonth: function() {
    today = new Date();
    today.setHours(0, 0, 0, 0);
    newDate = new Date(this.date);
    newDate.setDate(this.date.getDate() - this.daysNumber);
    newDate.setHours(0, 0, 0, 0);
    if (newDate < today)
        return;
    this.element.down('div#' + this.element.id + '_container').setOpacity(0.4);
    this.date.setDate(this.date.getDate() - this.daysNumber);
    console.log("this.date " + this.date);
    this.destroyCalendar();
    this.populate().refreshRange(true);
    this.element.down('div#' + this.element.id + '_container').setOpacity(1);
  },

  selectToday: function() {
    this.element.down('div#' + this.element.id + '_container').setOpacity(0.4);
    this.date = new Date();
    this.destroyCalendar();
    this.populate().refreshRange(true);
    this.element.down('div#' + this.element.id + '_container').setOpacity(1);
  },

  selectNextMonth: function() {
    this.element.down('div#' + this.element.id + '_container').setOpacity(0.4);
    this.date.setDate(this.date.getDate() + this.daysNumber);
    this.destroyCalendar();
    this.populate().refreshRange(true);
    this.element.down('div#' + this.element.id + '_container').setOpacity(1);
  },

  register: function() {
    this.buttonPrevious.observe('click', this.selectPreviousMonth.bind(this));
    this.buttonToday.observe('click', this.selectToday.bind(this));
    this.buttonNext.observe('click', this.selectNextMonth.bind(this));

    this.buttonPrevious.observe('custom:click', this.selectPreviousMonth.bind(this));
    this.buttonToday.observe('custom:click', this.selectToday.bind(this));
    this.buttonNext.observe('custom:click', this.selectNextMonth.bind(this));

    // mousemove listener for Opera in _disableTextSelection
    return this._disableTextSelection();
  },

  unregister: function() {
    this.element.select('td').each(function(day) { day.date = day.baseClass = null; });
  },

  _registerFieldObserver: function(fieldName) {
    //var field = this.fields.get(fieldName);
    //field.observe('focus', function() { field.hasFocus = true; this.parseField(fieldName, true); }.bind(this));
    //field.observe('blur', function() { this.refreshField(fieldName); }.bind(this));
    //new Form.Element.Observer(field, 0.2, function(element, value) { if (element.hasFocus) this.parseField(fieldName, true); }.bind(this));
    return this;
  },

  _disableTextSelection: function() {
    if (Prototype.Browser.IE) {
      this.element.onselectstart = function(event) {
        return false;
      };
    } else if (Prototype.Browser.Opera) {
      document.observe('mousemove', this.handleMouseMove.bind(this));
    } else {
      this.element.onmousedown = function(event) {
        if (!/input|textarea/i.test(Event.element(event).tagName)) return false;
      };
    }
    return this;
  },

  // Fields

  parseField: function(fieldName, populate) {
    /*var field = this.fields.get(fieldName);
    var date = Date.parseToObject(this.fields.get(fieldName).value);
    var failure = this.validateField(fieldName, date);
    if (failure != 'hard') {
      this.range.set(fieldName, date);
      field.removeClassName('error');
    } else if (field.hasFocus)
      field.addClassName('error');*/
    var date = Date.parseToObject(this.range.get(fieldName));
    this.date = date || new Date();
    if (populate && date) this.populate();
    return this;
  },

  refreshField: function(fieldName) {
    /*var field = this.fields.get(fieldName);
    var initValue = field.value;
    if (this.range.get(fieldName)) {
      field.value = typeof Date.CultureInfo == 'undefined' ? this.range.get(fieldName).strftime(this.format) : this.range.get(fieldName).toString(this.format);
    } else
      field.value = '';
    field.hasFocus && field.value == '' && initValue != '' ? field.addClassName('error') : field.removeClassName('error');
    field.hasFocus = false;*/
    return this;
  },

  validateField: function(fieldName, date) {
    if (!date) return;
    var error;
    if ((this.earliest && date < this.earliest) || (this.latest && date > this.latest))
      error = 'hard';
    else if (fieldName == 'start' && this.range.get('end') && date > this.range.get('end'))
      error = 'soft';
    else if (fieldName == 'end' && this.range.get('start') && date < this.range.get('start'))
      error = 'soft';
    return error;
  },

  // Event handling

  eventClick: function(event) {
    if (!event.element().ancestors) return;
    var el;
    if (el = event.findElement('a.timeframe_button'))
      this.handleButtonClick(event, el);
  },

  handleButtonClick: function(event, element) {
    var el;
    var movement = this.months > 1 ? this.months - 1 : 1;
    if (element.hasClassName('next'))
      this.date.setMonth(this.date.getMonth() + movement);
    else if (element.hasClassName('previous'))
      this.date.setMonth(this.date.getMonth() - movement);
    else if (element.hasClassName('today'))
      this.date = new Date();
    else if (element.hasClassName('reset'))
      this.reset();
    this.populate().refreshRange();
  },

  reset: function() {
    //this.fields.get('start').value = this.fields.get('start').defaultValue || '';
    //this.fields.get('end').value   = this.fields.get('end').defaultValue   || '';
    this.date = new Date(this.initDate);
    //this.parseField('start').refreshField('start').parseField('end').refreshField('end');
  },

  getPoint: function(date, hebPk) {
    if (this.range.get('start') && this.range.get('start').toString() == date && this.range.get('end'))
      this.startdrag = this.range.get('end');
    else {
      if (this.range.get('end') && this.range.get('end').toString() == date)
        this.startdrag = this.range.get('start');
      else
        this.startdrag = this.range.set('start', this.range.set('end', date));
    }
    this.range.set('hebPk', hebPk);
  },

  eventMouseOver: function(event) {
    var el;
    if (!this.dragging) this.toggleClearButton(event);
  },

  toggleClearButton: function(event) {
    var el;
    if (event.element().ancestors && event.findElement('td.selected')) {
      if (el = this.element.select('#calendar_0 .pre.selected').first());
      else if (el = this.element.select('.active.selected').first());
      if (el) Element.insert(el, { top: this.clearButton });
      this.clearButton.show().select('span').first().removeClassName('active');
    } else
      this.clearButton.hide();
  },

  eventMouseUp: function(event) {
    if (!this.dragging) {
        return;
    }
    if (!this.stuck) {
      this.dragging = false;
      if (event.findElement('span.clear span.active'))
       {
        // console.log('Clearing range !');
        this.clearRange();
       };
    }
    this.mousedown = false;
    var rangePk = this.range.get('hebPk');
    this.element.down('div#' + this.element.id + '_container').setOpacity(0.4);
    this.addDateRange();

    this.refreshRange(true, rangePk);
    this.element.down('div#' + this.element.id + '_container').setOpacity(1);
    // console.log('Clearing range !');
    this.clearRange();
  },
  clearRange: function() {
    this.clearButton.hide().select('span').first().removeClassName('active');
    this.range.set('start', this.range.set('end', null));
    this.range.set('hebPk', null);
    this.refreshField('start').refreshField('end');
  },
  checkSelectedDay: function() {
    if (this.range.get('hebPk') != null) toRefreshPks = [this.range.get('hebPk')];
    else toRefreshPks = this.hebsPks;
    currentDate = this.date;
    toRefreshPks.each(function(hebPk) {
        console.log("AJAX requesting " + hebPk);
        new Ajax.Request(
              '/selectedDays',
            {method: 'get',
             asynchronous: false,
             parameters: {hebPk: hebPk,
                          month:currentDate.getMonth()+1,
                          year:currentDate.getFullYear(),
                          range:3},
             onSuccess: function(transport) {
                  var json = transport.responseText.evalJSON();
                  var rented = [];
                  for (i=0;i<json.rented.length;++i){
                      rented.push(json.rented[i]);
                  };
                  Rented.set(hebPk, rented);
             }});
    });
  },

  refreshRange: function(refresh, refreshPk) {
    if (this.mousedown != true && refresh == true) this.checkSelectedDay();

    if (refreshPk) {
        // console.log("Refresh pk " + refreshPk);
        tableId = this.element.id + '_calendar_' + refreshPk;
        this.element.select('#' + tableId + ' td').each(function(day) {
            this.refreshCalendarRange(day);
        }.bind(this));
    }
    else {
        // console.log("Refresh all");
        this.element.select('td').each(function(day) {
            this.refreshCalendarRange(day);
        }.bind(this));
        
    }
    if (this.dragging) this.refreshField('start').refreshField('end');
  },

  refreshCalendarRange: function(day) {
      // day.writeAttribute('class', '');
      // day.addClassName(day.baseClass);
      rented = Rented.get(day.hebPk);
      if (rented && rented.contains(day.date.strftime('%Y-%m-%d'))){
        if (!day.hasClassName('indisp')) {
          day.addClassName('indisp');
        }
      }
      if (Prototype.Browser.Opera) {
        day.unselectable = 'on'; // Trick Opera into refreshing the selection (FIXME)
        day.unselectable = null;
      }
  },

  handleMouseMove: function(event) {
    if (event.findElement('#' + this.element.id + ' td')) window.getSelection().removeAllRanges(); // More Opera trickery
  }
});

Object.extend(Date, {
  parseToObject: function(string) {
    var date = Date.parse(string);
    if (!date) return null;
    date = new Date(date);
    return (date == 'Invalid Date' || date == 'NaN') ? null : date.neutral();
  }
});

Object.extend(Date.prototype, {
  // modified from http://alternateidea.com/blog/articles/2008/2/8/a-strftime-for-prototype
  strftime: function(format) {
    var day = this.getDay(), month = this.getMonth();
    var hours = this.getHours(), minutes = this.getMinutes();
    function pad(num) { return num.toPaddedString(2); };

    return format.gsub(/\%([aAbBcdHImMpSwyY])/, function(part) {
      switch(part[1]) {
        case 'a': return Locale.get('dayNames').invoke('substring', 0, 3)[day].escapeHTML(); break;
        case 'A': return Locale.get('dayNames')[day].escapeHTML(); break;
        case 'b': return Locale.get('monthNames').invoke('substring', 0, 3)[month].escapeHTML(); break;
        case 'B': return Locale.get('monthNames')[month].escapeHTML(); break;
        case 'c': return this.toString(); break;
        case 'd': return pad(this.getDate()); break;
        case 'H': return pad(hours); break;
        case 'I': return (hours % 12 == 0) ? 12 : pad(hours % 12); break;
        case 'm': return pad(month + 1); break;
        case 'M': return pad(minutes); break;
        case 'p': return hours >= 12 ? 'PM' : 'AM'; break;
        case 'S': return pad(this.getSeconds()); break;
        case 'w': return day; break;
        case 'y': return pad(this.getFullYear() % 100); break;
        case 'Y': return this.getFullYear().toString(); break;
      }
    }.bind(this));
  },

  neutral: function() {
    return new Date(this.getFullYear(), this.getMonth(), this.getDate(), 12);
  }
});
