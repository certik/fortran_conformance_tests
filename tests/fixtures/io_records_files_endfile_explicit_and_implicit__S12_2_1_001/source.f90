program io_rf_endfile_explicit_and_implicit
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.2.1-001
! covers: record-kind-formatted-unformatted-endfile
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u, v
  character(len=1) :: ch
  character(len=*), parameter :: name_close = 'io_records_files_implicit_close.dat'
  character(len=*), parameter :: name_open_a = 'io_records_files_implicit_open_a.dat'
  character(len=*), parameter :: name_open_b = 'io_records_files_implicit_open_b.dat'
  checks = 0
  call cleanup_name(name_close)
  call cleanup_name(name_open_a)
  call cleanup_name(name_open_b)

  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'explicit-open')
  write(u,'(A)',iostat=ios) 'E'
  call expect_zero(ios, 'explicit-write')
  endfile(u, iostat=ios)
  call expect_zero(ios, 'explicit-endfile')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'explicit-rewind')
  ch = '#'
  call expect_char(ch, '#', 'explicit-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'explicit-data-status')
  call expect_char(ch, 'E', 'explicit-data')
  ch = '!'
  call expect_char(ch, '!', 'explicit-end-pre')
  ios = -930
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'explicit-end-status')
  close(u)

  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'implicit-rewind-open')
  write(u,'(A)',iostat=ios) 'R'
  call expect_zero(ios, 'implicit-rewind-write')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'implicit-rewind')
  ch = '@'
  call expect_char(ch, '@', 'implicit-rewind-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-rewind-data-status')
  call expect_char(ch, 'R', 'implicit-rewind-data')
  ch = '$'
  call expect_char(ch, '$', 'implicit-rewind-end-pre')
  ios = -931
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-rewind-end')
  close(u)

  open(newunit=u, file=name_close, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-close-open')
  write(u,'(A)',iostat=ios) 'C'
  call expect_zero(ios, 'implicit-close-write')
  close(u, iostat=ios)
  call expect_zero(ios, 'implicit-close-close')
  open(newunit=u, file=name_close, status='old', form='formatted', action='read', iostat=ios)
  call expect_zero(ios, 'implicit-close-reopen')
  ch = '%'
  call expect_char(ch, '%', 'implicit-close-data-pre')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-close-data-status')
  call expect_char(ch, 'C', 'implicit-close-data')
  ch = '&'
  call expect_char(ch, '&', 'implicit-close-end-pre')
  ios = -932
  read(u,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-close-end')
  close(u, status='delete')

  open(newunit=u, file=name_open_a, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-open-first')
  write(u,'(A)',iostat=ios) 'O'
  call expect_zero(ios, 'implicit-open-write')
  open(unit=u, file=name_open_b, status='new', form='formatted', action='write', iostat=ios)
  call expect_zero(ios, 'implicit-open-second')
  close(u, status='delete')
  open(newunit=v, file=name_open_a, status='old', form='formatted', action='read', iostat=ios)
  call expect_zero(ios, 'implicit-open-reopen-first')
  ch = '?'
  call expect_char(ch, '?', 'implicit-open-data-pre')
  read(v,'(A)',iostat=ios) ch
  call expect_zero(ios, 'implicit-open-data-status')
  call expect_char(ch, 'O', 'implicit-open-data')
  ch = '~'
  call expect_char(ch, '~', 'implicit-open-end-pre')
  ios = -933
  read(v,'(A)',iostat=ios) ch
  call expect_end(ios, 'implicit-open-end')
  close(v, status='delete')
  call finish()
contains
  subroutine cleanup_name(name)
    character(len=*), intent(in) :: name
    integer :: cu, cios
    open(newunit=cu, file=name, status='replace', iostat=cios)
    if (cios == 0) close(cu, status='delete')
  end subroutine cleanup_name
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:int', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IORF:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IORF:length', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_zero(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= 0) then
      write(*,'(a,1x,a)') 'IORF:iostat-zero', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_zero
  subroutine expect_end(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= iostat_end) then
      write(*,'(a,1x,a)') 'IORF:iostat-end', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_end
  subroutine finish()
    if (checks /= 35) then
      write(*,'(a)') 'IORF:endfile_explicit_and_implicit:check-total'
      error stop 1
    end if
    write(*,'(a)') 'IO RECORDS FILES ENDFILE EXPLICIT AND IMPLICIT OK'
  end subroutine finish
end program io_rf_endfile_explicit_and_implicit
