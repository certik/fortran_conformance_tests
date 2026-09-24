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
program fixture_iolength_storage_units
  use io_positioning_internal_checks
  implicit none
  integer :: units_a, units_b, units_repeat, u, ios, value
  integer :: a, b
  a = 17
  b = -23
  inquire(iolength=units_a) a
  inquire(iolength=units_b) b
  inquire(iolength=units_repeat) a
  call check_true('iolength-positive', units_a > 0)
  call check_int('same-type-uniform-units', units_b, units_a)
  call check_int('repeat-iolength-stable', units_repeat, units_a)
  call check_true('file-storage-size-positive', file_storage_size > 0)
  open(newunit=u, status='scratch', access='direct', form='unformatted', recl=units_a, action='readwrite')
  write(u,rec=1) 909
  value = -7501
  call check_int('pre-direct-recl-read', value, -7501)
  read(u,rec=1,iostat=ios) value
  call check_int('direct-recl-read-status', ios, 0)
  call check_int('direct-recl-read-value', value, 909)
  close(u, status='delete')
  call finish(7)
  write(*,'(a)') 'IO POSITIONING INTERNAL IOLENGTH STORAGE UNITS OK'
end program fixture_iolength_storage_units
