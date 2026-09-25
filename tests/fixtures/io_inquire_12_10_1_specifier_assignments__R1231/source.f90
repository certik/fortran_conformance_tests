program p_specifier_assignments
  implicit none
  integer :: checks, u, du, ios, dummy_int, number, pos_value, size_value, nextrec_value, recl_value
  logical :: exists, opened, named, pending, dummy_logical
  character(len=28) :: name_stream, name_direct
  character(len=16) :: access, action, asynchronous, blank, decimal, delim, encoding, form
  character(len=16) :: formatted, name_value, pad, position, read_value, readwrite
  character(len=16) :: round_value, sequential, sign_value, stream_value, unformatted, write_value
  character(len=16) :: direct_value, dummy_char
  checks = 0
  name_stream = 'io_inquire_spec_stream.dat'
  name_direct = 'io_inquire_spec_direct.dat'
  call cleanup_name(name_stream)
  call cleanup_name(name_direct)
  open(newunit=u, file=name_stream, status='replace', access='stream', form='formatted', &
       action='readwrite', blank='zero', decimal='comma', delim='quote', encoding='default', &
       pad='no', round='up', sign='plus', iostat=ios)
  call expect_int(ios, 0, 'open-stream-status')

  access = '################' ! sentinel-probe:spec-access:  access = 'STREAM          ':  access = '                '
  call expect_char(access, '################', 'access-pre')
  action = '################' ! sentinel-probe:spec-action:  action = 'READWRITE       ':  action = '                '
  call expect_char(action, '################', 'action-pre')
  asynchronous = '################' ! sentinel-probe:sp-async:asynchronous='NO              ':asynchronous='                '
  call expect_char(asynchronous, '################', 'asynchronous-pre')
  blank = '################' ! sentinel-probe:spec-blank:  blank = 'ZERO            ':  blank = '                '
  call expect_char(blank, '################', 'blank-pre')
  decimal = '################' ! sentinel-probe:spec-decimal:  decimal = 'COMMA           ':  decimal = '                '
  call expect_char(decimal, '################', 'decimal-pre')
  delim = '################' ! sentinel-probe:spec-delim:  delim = 'QUOTE           ':  delim = '                '
  call expect_char(delim, '################', 'delim-pre')
  encoding = '################' ! sentinel-probe:spec-encoding:  encoding = 'DEFAULT         ':  encoding = '                '
  call expect_char(encoding, '################', 'encoding-pre')
  exists = .false. ! sentinel-probe:spec-exist:  exists = .true.:  exists = .true.
  call expect_logical(exists, .false., 'exist-pre')
  form = '################' ! sentinel-probe:spec-form:  form = 'FORMATTED       ':  form = '                '
  call expect_char(form, '################', 'form-pre')
  formatted = '################' ! sentinel-probe:spec-formatted:  formatted = 'YES             ':  formatted = '                '
  call expect_char(formatted, '################', 'formatted-pre')
  name_value = '################' ! sentinel-probe:spec-name:  name_value = 'changed-name    ':  name_value = '                '
  call expect_char(name_value, '################', 'name-pre')
  named = .false. ! sentinel-probe:spec-named:  named = .true.:  named = .true.
  call expect_logical(named, .false., 'named-pre')
  number = 0
  number = -777 ! sentinel-probe:spec-number:  number = -1:  number = 0
  call expect_int(number, -777, 'number-pre')
  opened = .false. ! sentinel-probe:spec-opened:  opened = .true.:  opened = .true.
  call expect_logical(opened, .false., 'opened-pre')
  pad = '################' ! sentinel-probe:spec-pad:  pad = 'NO              ':  pad = '                '
  call expect_char(pad, '################', 'pad-pre')
  pending = .true. ! sentinel-probe:spec-pending:  pending = .false.:  pending = .false.
  call expect_logical(pending, .true., 'pending-pre')
  pos_value = 0
  pos_value = -777 ! sentinel-probe:spec-pos:  pos_value = 1:  pos_value = 0
  call expect_int(pos_value, -777, 'pos-pre')
  position = '################' ! sentinel-probe:spec-position:  position = 'REWIND          ':  position = '                '
  call expect_char(position, '################', 'position-pre')
  read_value = '################' ! sentinel-probe:spec-read:  read_value = 'YES             ':  read_value = '                '
  call expect_char(read_value, '################', 'read-pre')
  readwrite = '################' ! sentinel-probe:spec-readwrite:  readwrite = 'YES             ':  readwrite = '                '
  call expect_char(readwrite, '################', 'readwrite-pre')
  round_value = '################' ! sentinel-probe:spec-round:  round_value = 'UP              ':  round_value = '                '
  call expect_char(round_value, '################', 'round-pre')
  sequential = '################' ! sentinel-probe:sp-seq:sequential='NO              ':sequential='                '
  call expect_char(sequential, '################', 'sequential-pre')
  sign_value = '################' ! sentinel-probe:spec-sign:  sign_value = 'PLUS            ':  sign_value = '                '
  call expect_char(sign_value, '################', 'sign-pre')
  size_value = -777 ! sentinel-probe:spec-size:  size_value = 0:  size_value = 0
  call expect_int(size_value, -777, 'size-pre')
  stream_value = '################' ! sentinel-probe:sp-stream:stream_value='YES             ':stream_value='                '
  call expect_char(stream_value, '################', 'stream-pre')
  unformatted = '################' ! sentinel-probe:sp-unfmt:unformatted='NO              ':unformatted='                '
  call expect_char(unformatted, '################', 'unformatted-pre')
  write_value = '################' ! sentinel-probe:spec-write:  write_value = 'YES             ':  write_value = '                '
  call expect_char(write_value, '################', 'write-pre')
  ios = -777 ! sentinel-probe:spec-iostat:  ios = 0:  ios = 0
  call expect_int(ios, -777, 'iostat-pre')
  dummy_char = '................'
  dummy_int = -909
  dummy_logical = .true.
  inquire(unit=u, access=access, action=action, asynchronous=asynchronous, blank=blank, &
          decimal=decimal, delim=delim, encoding=encoding, exist=exists, form=form, &
          formatted=formatted, name=name_value, named=named, number=number, opened=opened, &
          pad=pad, pending=pending, pos=pos_value, position=position, read=read_value, &
          readwrite=readwrite, round=round_value, sequential=sequential, sign=sign_value, &
          size=size_value, stream=stream_value, unformatted=unformatted, write=write_value, &
          iostat=ios)
  call expect_int(ios, 0, 'iostat-zero')
  call expect_char(access, 'STREAM          ', 'access-stream')
  call expect_char(action, 'READWRITE       ', 'action-readwrite')
  call expect_char(asynchronous, 'NO              ', 'asynchronous-no')
  call expect_char(blank, 'ZERO            ', 'blank-zero')
  call expect_char(decimal, 'COMMA           ', 'decimal-comma')
  call expect_char(delim, 'QUOTE           ', 'delim-quote')
  call expect_char(encoding, 'DEFAULT         ', 'encoding-default')
  call expect_logical(exists, .true., 'exist-true')
  call expect_char(form, 'FORMATTED       ', 'form-formatted')
  call expect_char(formatted, 'YES             ', 'formatted-yes')
  call expect_char_not(name_value, '################', 'name-assigned')
  call expect_logical(named, .true., 'named-true')
  call expect_int(number, u, 'number-value')
  call expect_logical(opened, .true., 'opened-true')
  call expect_char(pad, 'NO              ', 'pad-no')
  call expect_logical(pending, .false., 'pending-false')
  call expect_int(pos_value, 1, 'pos-one')
  call expect_char_not(position, '################', 'position-assigned')
  call expect_char(read_value, 'YES             ', 'read-yes')
  call expect_char(readwrite, 'YES             ', 'readwrite-yes')
  call expect_char(round_value, 'UP              ', 'round-up')
  call expect_char(sequential, 'NO              ', 'sequential-no')
  call expect_char(sign_value, 'PLUS            ', 'sign-plus')
  call expect_int_not(size_value, -777, 'size-assigned')
  call expect_char(stream_value, 'YES             ', 'stream-yes')
  call expect_char(unformatted, 'NO              ', 'unformatted-no')
  call expect_char(write_value, 'YES             ', 'write-yes')

  opened = .false. ! sentinel-probe:spec-file-opened:  opened = .true.:  opened = .true.
  call expect_logical(opened, .false., 'file-opened-pre')
  number = -777 ! sentinel-probe:spec-file-number:  number = -1:  number = 0
  call expect_int(number, -777, 'file-number-pre')
  inquire(file=name_stream, opened=opened, number=number)
  call expect_logical(opened, .true., 'file-opened-true')
  call expect_int(number, u, 'file-number-unit')
  close(u, status='delete')

  open(newunit=du, file=name_direct, status='replace', access='direct', form='formatted', &
       action='readwrite', recl=16, iostat=ios)
  call expect_int(ios, 0, 'open-direct-status')
  direct_value = '################' ! sentinel-probe:sp-direct:direct_value='YES             ':direct_value='                '
  call expect_char(direct_value, '################', 'direct-pre')
  nextrec_value = -777 ! sentinel-probe:spec-nextrec:  nextrec_value = 1:  nextrec_value = 0
  call expect_int(nextrec_value, -777, 'nextrec-pre')
  recl_value = -777 ! sentinel-probe:spec-recl:  recl_value = 16:  recl_value = 0
  call expect_int(recl_value, -777, 'recl-pre')
  inquire(unit=du, direct=direct_value, nextrec=nextrec_value, recl=recl_value)
  call expect_char(direct_value, 'YES             ', 'direct-yes')
  call expect_int(nextrec_value, 1, 'nextrec-one')
  call expect_int(recl_value, 16, 'recl-sixteen')
  close(du, status='delete')
  call finish()

contains
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'IOINQ:int', label, value, expected
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_int_not(value, forbidden, label)
    integer, intent(in) :: value, forbidden
    character(len=*), intent(in) :: label
    if (value == forbidden) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:int-not', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int_not
  subroutine expect_positive(value, label)
    integer, intent(in) :: value
    character(len=*), intent(in) :: label
    if (value <= 0) then
      write(*,'(a,1x,a,1x,i0)') 'IOINQ:positive', label, value
      error stop 1
    end if
    call pass(label)
  end subroutine expect_positive
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IOINQ:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IOINQ:char-len', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IOINQ:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_char_not(value, forbidden, label)
    character(len=*), intent(in) :: value, forbidden, label
    if (len(value) /= len(forbidden)) then
      write(*,'(a,1x,a)') 'IOINQ:char-not-len', label
      error stop 1
    end if
    if (value == forbidden) then
      write(*,'(a,1x,a)') 'IOINQ:char-not', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char_not
  subroutine cleanup_name(name)
    character(len=*), intent(in) :: name
    integer :: cu, cios
    logical :: ex
    inquire(file=name, exist=ex)
    if (ex) then
      open(newunit=cu, file=name, status='old', iostat=cios)
      if (cios == 0) close(cu, status='delete')
    end if
  end subroutine cleanup_name
  subroutine finish()
    if (checks /= 68) then
      write(*,'(a,1x,i0,1x,i0)') 'IOINQ:check-total', checks, 68
      error stop 1
    end if
    write(*,'(a)') 'IO INQUIRE SPECIFIER ASSIGNMENTS OK'
  end subroutine finish
end program p_specifier_assignments
