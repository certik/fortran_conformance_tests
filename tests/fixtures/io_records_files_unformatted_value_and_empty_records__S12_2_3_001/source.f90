program io_rf_unformatted_value_and_empty_records
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.2.3-001
! covers: unformatted-value-sequence unformatted-any-type-or-no-data
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u, first, second
  logical :: flag
  checks = 0
  ios = -920
  open(newunit=u, status='scratch', form='unformatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-unformatted')
  first = 0
  first = -701
  second = 0
  second = -702
  flag = .false.
  flag = .true.
  call expect_int(first, -701, 'first-pre')
  call expect_int(second, -702, 'second-pre')
  call expect_logical(flag, .true., 'flag-pre')
  write(u, iostat=ios) 137, .false.
  call expect_zero(ios, 'write-values')
  write(u, iostat=ios)
  call expect_zero(ios, 'write-empty-unformatted')
  write(u, iostat=ios) 246
  call expect_zero(ios, 'write-second')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'rewind-unformatted')
  read(u, iostat=ios) first, flag
  call expect_zero(ios, 'read-values-status')
  call expect_int(first, 137, 'first-read')
  call expect_logical(flag, .false., 'flag-read')
  read(u, iostat=ios)
  call expect_zero(ios, 'read-empty-unformatted')
  read(u, iostat=ios) second
  call expect_zero(ios, 'read-second-status')
  call expect_int(second, 246, 'second-read')
  close(u)
  call finish()
contains
  subroutine pass(label)
    character(len=*), intent(in) :: label
    checks = checks + 1
  end subroutine pass
  subroutine expect_int(value, expected, label)
    integer, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:int', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_int
  subroutine expect_logical(value, expected, label)
    logical, intent(in) :: value, expected
    character(len=*), intent(in) :: label
    if (value .neqv. expected) then
      write(*,'(a,1x,a)') 'IORF:logical', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_logical
  subroutine expect_char(value, expected, label)
    character(len=*), intent(in) :: value, expected, label
    if (len(value) /= len(expected)) then
      write(*,'(a,1x,a)') 'IORF:length', label
      error stop 1
    end if
    if (value /= expected) then
      write(*,'(a,1x,a)') 'IORF:char', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_char
  subroutine expect_zero(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= 0) then
      write(*,'(a,1x,a)') 'IORF:iostat-zero', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_zero
  subroutine expect_end(status, label)
    integer, intent(in) :: status
    character(len=*), intent(in) :: label
    if (status /= iostat_end) then
      write(*,'(a,1x,a)') 'IORF:iostat-end', label
      error stop 1
    end if
    call pass(label)
  end subroutine expect_end
  subroutine finish()
    if (checks /= 14) then
      write(*,'(a)') 'IORF:unformatted_value_and_empty_records:check-total'
      error stop 1
    end if
    write(*,'(a)') 'IO RECORDS FILES UNFORMATTED VALUE AND EMPTY RECORDS OK'
  end subroutine finish
end program io_rf_unformatted_value_and_empty_records
