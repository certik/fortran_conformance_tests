program io_rf_internal_formatted_transfer
  use, intrinsic :: iso_fortran_env, only: iostat_end
  implicit none
! rule: S12.2.1-001
! covers: record-character-sequence record-kind-formatted-unformatted-endfile
! extra coverage listed in tools/generate_io_records_files_fixtures.py
  integer :: checks, ios, n
  character(len=5) :: record
  character(len=1) :: letter
  checks = 0
  record = '#####'
  n = -777
  letter = 'Z'
  ios = -900
  call expect_int(n, -777, 'n-pre')
  call expect_char(letter, 'Z', 'letter-pre')
  call expect_char(record, '#####', 'record-pre')
  write(record,'(I3,1X,A)',iostat=ios) 137, 'Q'
  call expect_zero(ios, 'write-internal')
  call expect_int(len(record), 5, 'record-len')
  call expect_char(record, '137 Q', 'record-text')
  ios = -901
  read(record,'(I3,1X,A)',iostat=ios) n, letter
  call expect_zero(ios, 'read-internal')
  call expect_int(n, 137, 'n-read')
  call expect_char(letter, 'Q', 'letter-read')
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
    if (checks /= 9) then
      write(*,'(a)') 'IORF:internal_formatted_transfer:check-total'
      error stop 1
    end if
    write(*,'(a)') 'IO RECORDS FILES INTERNAL FORMATTED TRANSFER OK'
  end subroutine finish
end program io_rf_internal_formatted_transfer
