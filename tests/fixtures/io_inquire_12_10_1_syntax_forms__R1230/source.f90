program p_syntax_forms
  implicit none
  integer :: checks, iol, ios, u, values(2), got(2)
  logical :: opened
  checks = 0
  opened = .true. ! sentinel-probe:syntax-opened:  opened = .false.:  opened = .false.
  call expect_logical(opened, .true., 'opened-pre')
  inquire(unit=10, opened=opened)
  call expect_logical(opened, .false., 'inquire-spec-list-form')
  values = [31, 32]
  got = [-1, -1]
  iol = -777 ! sentinel-probe:syntax-iolength:  iol = 8:  iol = 0
  call expect_int(iol, -777, 'iolength-pre')
  inquire(iolength=iol) values
  call expect_positive(iol, 'iolength-output-list-form')
  open(newunit=u, file='io_inquire_r1230_direct.dat', status='replace', access='direct', &
       form='unformatted', recl=iol, iostat=ios)
  call expect_int(ios, 0, 'open-direct')
  write(u, rec=1, iostat=ios) values
  call expect_int(ios, 0, 'write-direct')
  read(u, rec=1, iostat=ios) got
  call expect_int(ios, 0, 'read-direct')
  call expect_int(got(1), 31, 'got-one')
  call expect_int(got(2), 32, 'got-two')
  close(u, status='delete')
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
    if (checks /= 9) then
      write(*,'(a,1x,i0,1x,i0)') 'IOINQ:check-total', checks, 9
      error stop 1
    end if
    write(*,'(a)') 'IO INQUIRE SYNTAX FORMS OK'
  end subroutine finish
end program p_syntax_forms
