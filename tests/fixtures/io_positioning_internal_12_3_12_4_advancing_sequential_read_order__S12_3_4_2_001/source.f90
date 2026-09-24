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
program fixture_advancing_sequential_read_order
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios, first, second, again
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(I0)') 11
  write(u,'(I0)') 22
  rewind u
  first = -7101
  call check_int('pre-first-record', first, -7101)
  read(u,*,iostat=ios) first
  call check_int('first-read-status', ios, 0)
  call check_int('first-read-value', first, 11)
  second = -7102
  call check_int('pre-second-record', second, -7102)
  read(u,*,iostat=ios) second
  call check_int('second-read-status', ios, 0)
  call check_int('second-read-value', second, 22)
  backspace u
  again = -7103
  call check_int('pre-backspace-reread', again, -7103)
  read(u,*,iostat=ios) again
  call check_int('backspace-reread-status', ios, 0)
  call check_int('backspace-reread-value', again, 22)
  close(u, status='delete')
  call finish(9)
  write(*,'(a)') 'IO POSITIONING INTERNAL ADVANCING SEQUENTIAL READ ORDER OK'
end program fixture_advancing_sequential_read_order
