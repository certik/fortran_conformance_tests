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
program fixture_sequential_output_truncates_following
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios, first, rewritten, eof_probe
  open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
  write(u,'(I0)') 10
  write(u,'(I0)') 20
  write(u,'(I0)') 30
  rewind u
  first = -7201
  call check_int('pre-existing-first', first, -7201)
  read(u,*,iostat=ios) first
  call check_int('existing-first-status', ios, 0)
  call check_int('existing-first-value', first, 10)
  write(u,'(I0)') 15
  rewind u
  first = -7202
  call check_int('pre-final-first', first, -7202)
  read(u,*,iostat=ios) first
  call check_int('final-first-status', ios, 0)
  call check_int('final-first-value', first, 10)
  rewritten = -7203
  call check_int('pre-rewritten-next', rewritten, -7203)
  read(u,*,iostat=ios) rewritten
  call check_int('rewritten-next-status', ios, 0)
  call check_int('rewritten-next-value', rewritten, 15)
  eof_probe = -7204
  call check_int('pre-output-eof', eof_probe, -7204)
  read(u,*,iostat=ios) eof_probe
  call check_int('output-truncated-eof', ios, iostat_end)
  close(u, status='delete')
  call finish(11)
  write(*,'(a)') 'IO POSITIONING INTERNAL SEQUENTIAL OUTPUT TRUNCATES FOLLOWING OK'
end program fixture_sequential_output_truncates_following
