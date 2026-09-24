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
program fixture_unformatted_stream_terminal_size
  use io_positioning_internal_checks
  implicit none
  integer :: u, pos_after_empty, pos_after_write, size_after_write, ios
  character(len=1) :: ch
  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=3)
  inquire(unit=u, pos=pos_after_empty)
  call check_int('empty-output-position', pos_after_empty, 3)
  write(u,pos=5) 'Z'
  inquire(unit=u, pos=pos_after_write, size=size_after_write, iostat=ios)
  call check_int('terminal-inquire-status', ios, 0)
  call check_true('terminal-size-extended', size_after_write >= 5)
  call check_true('terminal-position-after-write', pos_after_write > 5)
  ch = '#'
  call check_char('pre-terminal-readback', ch, '#')
  read(u,pos=5,iostat=ios) ch
  call check_int('terminal-readback-status', ios, 0)
  call check_char('terminal-readback-value', ch, 'Z')
  close(u, status='delete')
  call finish(7)
  write(*,'(a)') 'IO POSITIONING INTERNAL UNFORMATTED STREAM TERMINAL SIZE OK'
end program fixture_unformatted_stream_terminal_size
