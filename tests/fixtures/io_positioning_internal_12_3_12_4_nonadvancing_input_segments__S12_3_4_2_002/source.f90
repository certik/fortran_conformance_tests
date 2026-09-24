module io_positioning_internal_checks
  use, intrinsic :: iso_fortran_env, only: iostat_end, iostat_eor, file_storage_size
  implicit none
  integer :: checks = 0
contains
  subroutine fail(label)
    character(len=*), intent(in) :: label
    write(*,'(a,1x,a)') 'CHECK_FAILED', label
    error stop 99
  end subroutine
  subroutine check_int(label, actual, expected)
    character(len=*), intent(in) :: label
    integer, intent(in) :: actual, expected
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_INT', label, actual, expected
      error stop 1
    end if
    checks = checks + 1
  end subroutine
  subroutine check_true(label, actual)
    character(len=*), intent(in) :: label
    logical, intent(in) :: actual
    if (.not. actual) call fail(label)
    checks = checks + 1
  end subroutine
  subroutine check_char(label, actual, expected)
    character(len=*), intent(in) :: label
    character(len=*), intent(in) :: actual, expected
    if (len(actual) /= len(expected)) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_CHAR_LEN', label, len(actual), len(expected)
      error stop 2
    end if
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,"[",a,"] [",a,"]")') 'CHECK_CHAR', label, actual, expected
      error stop 3
    end if
    checks = checks + 1
  end subroutine
  subroutine finish(expected)
    integer, intent(in) :: expected
    if (checks /= expected) then
      write(*,'(a,1x,i0,1x,i0)') 'CHECK_COUNT', checks, expected
      error stop 4
    end if
  end subroutine
end module io_positioning_internal_checks
program fixture_nonadvancing_input_segments
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios, got
  character(len=3) :: first, second
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)') 'ABCDEF'
  write(u,'(A)') 'NEXT'
  rewind u
  first = '###'
  call check_char('pre-first-segment', first, '###')
  read(u,'(A3)',advance='no',size=got,iostat=ios) first
  call check_int('first-segment-status', ios, 0)
  call check_int('first-segment-size', got, 3)
  call check_char('first-segment-text', first, 'ABC')
  second = '@@@'
  call check_char('pre-second-segment', second, '@@@')
  read(u,'(A3)',advance='no',size=got,iostat=ios) second
  call check_int('second-segment-status', ios, 0)
  call check_int('second-segment-size', got, 3)
  call check_char('second-segment-text', second, 'DEF')
  close(u, status='delete')
  call finish(8)
  write(*,'(a)') 'IO POSITIONING INTERNAL NONADVANCING INPUT SEGMENTS OK'
end program fixture_nonadvancing_input_segments
