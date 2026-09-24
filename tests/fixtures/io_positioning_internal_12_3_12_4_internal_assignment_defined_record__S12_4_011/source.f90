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
program fixture_internal_assignment_defined_record
  use io_positioning_internal_checks
  implicit none
  integer :: ios, number
  character(len=5) :: record
  character(len=1) :: tag
  record = '246 R'
  call check_char('assigned-record-text', record, '246 R')
  number = -7701
  tag = '#'
  call check_int('pre-assigned-number', number, -7701)
  call check_char('pre-assigned-tag', tag, '#')
  read(record,'(I3,1X,A1)',iostat=ios) number, tag
  call check_int('assigned-read-status', ios, 0)
  call check_int('assigned-number-value', number, 246)
  call check_char('assigned-tag-value', tag, 'R')
  call finish(6)
  write(*,'(a)') 'IO POSITIONING INTERNAL INTERNAL ASSIGNMENT DEFINED RECORD OK'
end program fixture_internal_assignment_defined_record
