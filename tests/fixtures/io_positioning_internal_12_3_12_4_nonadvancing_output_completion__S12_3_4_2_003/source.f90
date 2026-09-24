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
program fixture_nonadvancing_output_completion
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios
  character(len=4) :: closed_record
  character(len=3) :: rewind_record
  character(len=4) :: combined
  character(len=*), parameter :: name1 = 'batch284_nonadvancing_close.dat'
  character(len=*), parameter :: name2 = 'batch284_nonadvancing_rewind.dat'
  open(newunit=u, file=name1, status='replace', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'CLO'
  close(u)
  open(newunit=u, file=name1, status='old', access='sequential', form='formatted', action='read')
  closed_record = '####'
  call check_char('pre-closed-record', closed_record, '####')
  read(u,'(A4)',iostat=ios) closed_record
  call check_int('closed-record-status', ios, 0)
  call check_char('closed-record-text', closed_record, 'CLO ')
  close(u, status='delete')

  open(newunit=u, file=name2, status='replace', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'RE'
  rewind u
  rewind_record = '@@@'
  call check_char('pre-rewind-record', rewind_record, '@@@')
  read(u,'(A3)',iostat=ios) rewind_record
  call check_int('rewind-record-status', ios, 0)
  call check_char('rewind-record-text', rewind_record, 'RE ')
  close(u, status='delete')

  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(A)',advance='no') 'AA'
  write(u,'(A)',advance='no') 'BB'
  rewind u
  combined = '????'
  call check_char('pre-combined-output', combined, '????')
  read(u,'(A4)',iostat=ios) combined
  call check_int('combined-output-status', ios, 0)
  call check_char('combined-output-text', combined, 'AABB')
  close(u, status='delete')
  call finish(9)
  write(*,'(a)') 'IO POSITIONING INTERNAL NONADVANCING OUTPUT COMPLETION OK'
end program fixture_nonadvancing_output_completion
