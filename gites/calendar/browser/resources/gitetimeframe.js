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
var Rented = [];
var GiteTimeframe = Class.create({
  Version: '0.2',

  initialize: function(element, options) {
    Timeframes.push(this);

    this.element = $(element);
    this.element.addClassName('timeframe_calendar');
    this.options = $H({ months: 1 }).merge(options || {});
    this.language     = this.options.get('language');
    this.months = this.options.get('months');
    this.weekdayNames = days.get(this.language);
    this.monthNames   = months.get(this.language);
    this.format       = this.options.get('format')     || Locale.get('format');
    this.weekOffset   = this.options.get('weekOffset') || Locale.get('weekOffset');
    this.hebPk        = this.options.get('hebPk');
    this.maxRange = 99999;

    this.buttons = $H({
      previousYear: $H({ label: '&nbsp;', element: $(this.options.get('previousYearButton')) }),
      previous:     $H({ label: '&nbsp;', element: $(this.options.get('previousButton')) }),
      today:        $H({ label: '&nbsp;', element: $(this.options.get('todayButton')) }),
      next:         $H({ label: '&nbsp;', element: $(this.options.get('nextButton')) }),
      nextYear:     $H({ label: '&nbsp;', element: $(this.options.get('nextYearButton')) })
    });
    //this.fields = $H({ start: $(this.options.get('startField')), end: $(this.options.get('endField')) });

   this.range = $H({});
    this._buildButtons()._buildFields();
    this.earliest = Date.parseToObject(this.options.get('earliest'));
    this.latest   = Date.parseToObject(this.options.get('latest'));

    this.calendars = [];
    this.element.insert(new Element('div', { id: this.element.id + '_container' }));
    this.months.times(function(month) { this.createCalendar(month); }.bind(this));

    this.register().populate().refreshRange();
  },

  // Scaffolding

  createCalendar: function() {
    var calendar = new Element('table', {
      id: this.element.id + '_calendar_' + this.calendars.length, border: 0, cellspacing: 0, cellpadding: 5
    });
    calendar.insert(new Element('caption'));

    var head = new Element('thead');
    var row  = new Element('tr');
    this.weekdayNames.length.times(function(column) {
      var weekday = this.weekdayNames[(column + this.weekOffset) % 7];
      var cell = new Element('th', { scope: 'col', abbr: weekday }).update(weekday.substring(0,1));
      row.insert(cell);
    }.bind(this));
    head.insert(row);
    calendar.insert(head);

    var body = new Element('tbody');
    (6).times(function(rowNumber) {
      var row = new Element('tr');
      this.weekdayNames.length.times(function(column) {
        var cell = new Element('td');
        row.insert(cell);
      });
      body.insert(row);
    }.bind(this));
    calendar.insert(body);

    this.element.down('div#' + this.element.id + '_container').insert(calendar);
    this.calendars.push(calendar);
    this.months = this.calendars.length;
    return this;
  },

  destroyCalendar: function() {
    this.calendars.pop().remove();
    this.months = this.calendars.length;
    return this;
  },

  populate: function() {
    var month = this.date.neutral();
    month.setDate(1);
    this.calendars.each(function(calendar) {
      var caption = calendar.select('caption').first();
      caption.update(this.monthNames[month.getMonth()] + ' ' + month.getFullYear());
      var iterator = new Date(month);
      var offset = (iterator.getDay() - this.weekOffset) % 7;
      var inactive = offset > 0 ? 'pre beyond' : false;
      iterator.setDate(iterator.getDate() - offset);
      if (iterator.getDate() > 1 && !inactive) {
        iterator.setDate(iterator.getDate() - 7);
        if (iterator.getDate() > 1) inactive = 'pre beyond';
      }

      calendar.select('td').each(function(day) {
        day.date = new Date(iterator); // Is this expensive (we unload these later)? We could store the epoch time instead.
        day.update(day.date.getDate()).writeAttribute('class', '');

        if (day.hasClassName('active')) day.removeClassName('active');
        if (day.hasClassName('inactive')) day.removeClassName('inactive');
        if (day.hasClassName('unselectable')) day.removeClassName('unselectable');
        if (day.hasClassName('selectable')) day.removeClassName('selectable');
        if (day.hasClassName('today')) day.removeClassName('today');
        if (day.hasClassName('post')) day.removeClassName('post');
        if (day.hasClassName('pre')) day.removeClassName('pre');
        if (day.hasClassName('beyond')) day.removeClassName('beyond');
        if (day.hasClassName('indisp')) day.removeClassName('indisp');
        
        if (inactive) day.addClassName(inactive);
        else day.addClassName('active');
        if ((this.earliest && day.date < this.earliest) || (this.latest && day.date > this.latest))
          day.addClassName('unselectable');
        else
          day.addClassName('selectable');
        if (iterator.toString() === new Date().neutral().toString()) day.addClassName('today');  
        day.baseClass = day.readAttribute('class');

        iterator.setDate(iterator.getDate() + 1);
        if (iterator.getDate() == 1) inactive = inactive ? false : 'post beyond';
      }.bind(this));

      month.setMonth(month.getMonth() + 1);
    }.bind(this));
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
          case 1: this.buttonPreviousYear = button;
          case 2: this.buttonPrevious = button;
          case 3: this.buttonToday = button;
          case 4: this.buttonNext = button;
          case 5: this.buttonNextYear = button;
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

  selectPreviousYear: function() {
    firstDayOfThisMonth = new Date();
    this.truncateDate(firstDayOfThisMonth);
    newYear = this.date.getFullYear() - 1
    newDate = new Date(this.date);
    newDate.setYear(newYear);
    this.truncateDate(newDate);
    if (newDate.equalsTo(firstDayOfThisMonth) || (newDate > firstDayOfThisMonth))
      this.date.setYear(newYear);
    else
      return ;
    this.populate().refreshRange();
  },

  selectPreviousMonth: function() {
    var movement = this.months > 1 ? this.months - 1 : 1;
    firstDayOfThisMonth = new Date();
    this.truncateDate(firstDayOfThisMonth);
    newMonth = this.date.getMonth() - movement;
    newDate = new Date(this.date);
    newDate.setMonth(newMonth);
    this.truncateDate(newDate);
    if (newDate.equalsTo(firstDayOfThisMonth) || (newDate > firstDayOfThisMonth))
      this.date.setMonth(newMonth);
    else
      return ;
    this.populate().refreshRange();
  },

  selectToday: function() {
    today = new Date();
    month = today.getMonth();
    year = today.getFullYear();
    existingMonth = this.date.getMonth();
    existingYear = this.date.getFullYear();
    if (month != existingMonth || year != existingYear)
      this.date = today;
    else
      return ;
    this.populate().refreshRange();
  },

  selectNextMonth: function() {
    var movement = this.months > 1 ? this.months - 1 : 1;
    this.date.setMonth(this.date.getMonth() + movement);
    this.populate().refreshRange();
  },

  selectNextYear: function() {
    this.date.setYear(this.date.getFullYear() + 1);
    this.populate().refreshRange();
  },

  register: function() {
    this.buttonPrevious.observe('click', this.selectPreviousMonth.bind(this));
    this.buttonPreviousYear.observe('click', this.selectPreviousYear.bind(this));
    this.buttonToday.observe('click', this.selectToday.bind(this));
    this.buttonNext.observe('click', this.selectNextMonth.bind(this));
    this.buttonNextYear.observe('click', this.selectNextYear.bind(this));

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

  truncateDate: function(date) {
    date.setDate(1);
    date.setHours(0, 0, 0, 0);
  },

  handleButtonClick: function(event, element) {
    var el;
    var movement = this.months > 1 ? this.months - 1 : 1;
    if (element.hasClassName('next'))
      this.date.setMonth(this.date.getMonth() + movement);
    else if (element.hasClassName('previous')) {
      firstDayOfThisMonth = new Date();
      this.truncateDate(firstDayOfThisMonth);
      newMonth = this.date.getMonth() - movement;
      newDate = new Date(this.date);
      newDate.setMonth(newMonth);
      this.truncateDate(newDate);
      if (newDate.equalsTo(firstDayOfThisMonth) || (newDate > firstDayOfThisMonth))
        this.date.setMonth(newMonth);
      else
        return ;
    }
    else if (element.hasClassName('today'))
      this.date = new Date();

    this.populate().refreshRange();
  },

  getPoint: function(date) {
    if (this.range.get('start') && this.range.get('start').toString() == date && this.range.get('end'))
      this.startdrag = this.range.get('end');
    else {
      if (this.range.get('end') && this.range.get('end').toString() == date)
        this.startdrag = this.range.get('start');
      else
        this.startdrag = this.range.set('start', this.range.set('end', date));
    }
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
        this.clearRange();
    }
    this.mousedown = false;
    this.addDateRange();
    this.checkSelectedDay();
    this.refreshRange();
  },

  clearRange: function() {
    this.clearButton.hide().select('span').first().removeClassName('active');
    this.range.set('start', this.range.set('end', null));
    this.refreshField('start').refreshField('end');
  },

  checkSelectedDay: function() {
    new Ajax.Request(
        '/selectedDays',
        {method: 'get',
         asynchronous: false,
         parameters: {hebPk:this.hebPk,
                      month:this.date.getMonth()+1,
                      year:this.date.getFullYear(),
                      range:this.months},
         onSuccess: function(transport) {
              Rented.clear();
              var json = transport.responseText.evalJSON();
              for (i=0;i<json.rented.length;++i){
                  Rented.push(json.rented[i]);
              };
         }});
  },

  refreshRange: function() {
    if (this.mousedown != true) this.checkSelectedDay();
    this.element.select('td').each(function(day) {
      // day.writeAttribute('class', '');
      // day.addClassName(day.baseClass);
      if (Rented.contains(day.date.strftime('%Y-%m-%d'))){
        if (!day.hasClassName('indisp')) {
          day.addClassName('indisp');
        }
      }
      if (Prototype.Browser.Opera) {
        day.unselectable = 'on'; // Trick Opera into refreshing the selection (FIXME)
        day.unselectable = null;
      }
    }.bind(this));
    if (this.dragging) this.refreshField('start').refreshField('end');
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
Date.prototype.equalsTo = function(date) {
  return ((this.getFullYear() == date.getFullYear()) &&
    (this.getMonth() == date.getMonth()) &&
    (this.getDate() == date.getDate()) &&
    (this.getHours() == date.getHours()) &&
    (this.getMinutes() == date.getMinutes()));
};

Object.extend(Date.prototype, {
  equalsTo: function(date) {
  return ((this.getFullYear() == date.getFullYear()) &&
    (this.getMonth() == date.getMonth()) &&
    (this.getDate() == date.getDate()) &&
    (this.getHours() == date.getHours()) &&
    (this.getMinutes() == date.getMinutes()));
  },
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
