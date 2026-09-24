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
program fixture_direct_access_rec_positions
  use io_positioning_internal_checks
  implicit none
  integer :: u, ios, recl, sample, selected, first
  sample = 0
  inquire(iolength=recl) sample
  open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
  write(u,rec=1) 111
  write(u,rec=3) 333
  selected = -7301
  call check_int('pre-direct-selected', selected, -7301)
  read(u,rec=3,iostat=ios) selected
  call check_int('direct-selected-status', ios, 0)
  call check_int('direct-selected-value', selected, 333)
  first = -7302
  call check_int('pre-direct-first', first, -7302)
  read(u,rec=1,iostat=ios) first
  call check_int('direct-first-status', ios, 0)
  call check_int('direct-first-value', first, 111)
  close(u, status='delete')
  call finish(6)
  write(*,'(a)') 'IO POSITIONING INTERNAL DIRECT ACCESS REC POSITIONS OK'
end program fixture_direct_access_rec_positions
