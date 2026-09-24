program io_rf_named_file_create_delete_inquire
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.3.2-004
! covers: inquire-may-reference-nonexistent-file open-may-reference-nonexistent-file
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u
  logical :: exists
  character(len=*), parameter :: name = 'io_records_files_named_create_delete.dat'
  checks = 0
  call cleanup_name(name)
  exists = .false.
  exists = .true.
  call expect_logical(exists, .true., 'exists-before-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .false., 'exists-before')
  ios = -940
  open(newunit=u, file=name, status='new', form='formatted', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-new')
  write(u,'(A)',iostat=ios) 'N'
  call expect_zero(ios, 'write-named')
  exists = .true.
  exists = .false.
  call expect_logical(exists, .false., 'exists-after-open-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .true., 'exists-after-open')
  close(u, status='delete', iostat=ios)
  call expect_zero(ios, 'close-delete')
  exists = .false.
  exists = .true.
  call expect_logical(exists, .true., 'exists-after-delete-sentinel')
  inquire(file=name, exist=exists)
  call expect_logical(exists, .false., 'exists-after-delete')
  call finish()
contains
  subroutine cleanup_name(path)
    character(len=*), intent(in) :: path
    integer :: cu, cios
    open(newunit=cu, file=path, status='replace', iostat=cios)
    if (cios == 0) close(cu, status='delete')
  end subroutine cleanup_name
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
    if (checks /= 9) then
      write(*,'(a)') 'IORF:named_file_create_delete_inquire:check-total'
      error stop 1
    end if
    write(*,'(a)') 'IO RECORDS FILES NAMED FILE CREATE DELETE INQUIRE OK'
  end subroutine finish
end program io_rf_named_file_create_delete_inquire
