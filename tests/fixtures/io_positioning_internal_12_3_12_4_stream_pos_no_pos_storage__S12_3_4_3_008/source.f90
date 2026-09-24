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
program fixture_stream_pos_no_pos_storage
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios, char_units, second_pos, int_value
  character(len=1) :: ch
  inquire(iolength=char_units) ch
  second_pos = 1 + char_units
  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=1) 'A'
  write(u,pos=second_pos) 'B'
  ch = '#'
  call check_char('pre-stream-pos-second', ch, '#')
  read(u,pos=second_pos,iostat=ios) ch
  call check_int('stream-pos-second-status', ios, 0)
  call check_char('stream-pos-second-value', ch, 'B')
  ch = '@'
  call check_char('pre-stream-pos-first', ch, '@')
  read(u,pos=1,iostat=ios) ch
  call check_int('stream-pos-first-status', ios, 0)
  call check_char('stream-pos-first-value', ch, 'A')
  ch = '?'
  call check_char('pre-stream-no-pos', ch, '?')
  read(u,iostat=ios) ch
  call check_int('stream-no-pos-status', ios, 0)
  call check_char('stream-no-pos-value', ch, 'B')
  close(u, status='delete')

  open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
  write(u,pos=2) 2468
  int_value = -7401
  call check_int('pre-unaligned-integer', int_value, -7401)
  read(u,pos=2,iostat=ios) int_value
  call check_int('unaligned-integer-status', ios, 0)
  call check_int('unaligned-integer-value', int_value, 2468)
  close(u, status='delete')
  call finish(12)
  write(*,'(a)') 'IO POSITIONING INTERNAL STREAM POS NO POS STORAGE OK'
end program fixture_stream_pos_no_pos_storage
