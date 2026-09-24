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
program fixture_internal_array_records_position
  use io_positioning_internal_checks
  implicit none
  integer :: ios
  character(len=5) :: records(3), first_again, first_third
  records = '@@@@@'
  call check_char('pre-array-record-one', records(1), '@@@@@')
  write(records,'(A)') 'AA', 'BB', 'CC'
  call check_int('array-record-len-one', len(records(1)), 5)
  call check_char('array-record-one-text', records(1), 'AA   ')
  call check_char('array-record-two-text', records(2), 'BB   ')
  call check_char('array-record-three-text', records(3), 'CC   ')
  first_again = '#####'
  call check_char('pre-array-read-first', first_again, '#####')
  read(records,'(A)',iostat=ios) first_again
  call check_int('array-read-first-status', ios, 0)
  call check_char('array-read-first-text', first_again, 'AA   ')
  first_third = '?????'
  call check_char('pre-array-reread-first', first_third, '?????')
  read(records,'(A)',iostat=ios) first_third
  call check_int('array-reread-first-status', ios, 0)
  call check_char('array-reread-first-text', first_third, 'AA   ')
  call finish(11)
  write(*,'(a)') 'IO POSITIONING INTERNAL INTERNAL ARRAY RECORDS POSITION OK'
end program fixture_internal_array_records_position
