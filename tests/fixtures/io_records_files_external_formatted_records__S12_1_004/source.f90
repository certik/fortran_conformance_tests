program io_rf_external_formatted_records
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.1-004
! covers: record-file-composition
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, u
  character(len=1) :: ch
  logical :: opened
  checks = 0
  opened = .true.
  call expect_logical(opened, .true., 'opened-pre')
  inquire(unit=u, opened=opened)
  call expect_logical(opened, .false., 'opened-inquire')
  ios = -910
  open(newunit=u, status='scratch', form='formatted', access='sequential', action='readwrite', iostat=ios)
  call expect_zero(ios, 'open-scratch')
  write(u,'(A)',iostat=ios) 'A'
  call expect_zero(ios, 'write-a')
  write(u,'()',iostat=ios)
  call expect_zero(ios, 'write-empty')
  write(u,'(A)',iostat=ios) 'B'
  call expect_zero(ios, 'write-b')
  rewind(u, iostat=ios)
  call expect_zero(ios, 'rewind')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-a')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-a-status')
  call expect_char(ch, 'A', 'read-a')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-empty')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-empty-status')
  call expect_char(ch, ' ', 'read-empty')
  ch = '#'
  call expect_char(ch, '#', 'ch-pre-b')
  read(u,'(A)',iostat=ios) ch
  call expect_zero(ios, 'read-b-status')
  call expect_char(ch, 'B', 'read-b')
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
    if (checks /= 16) then
      write(*,'(a)') 'IORF:external_formatted_records:check-total'
      error stop 1
    end if
    write(*,'(a)') 'IO RECORDS FILES EXTERNAL FORMATTED RECORDS OK'
  end subroutine finish
end program io_rf_external_formatted_records
