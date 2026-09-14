! rule: S6.3.2.2-005
! covers: end-file
! evidence: positive-control
program endfile_spellings
  implicit none
  integer :: unit, status, value
  open(newunit=unit, status='scratch', action='readwrite', &
       access='sequential', form='formatted', iostat=status)
  if (status /= 0) stop 1
  write(unit, '(I1)', iostat=status) 7
  if (status /= 0) stop 2
  endfile(unit, iostat=status)
  if (status /= 0) stop 3
  rewind(unit, iostat=status)
  if (status /= 0) stop 4
  read(unit, '(I1)', iostat=status) value
  if (status /= 0) stop 5
  if (value /= 7) stop 6
  end file(unit, iostat=status)
  if (status /= 0) stop 7
  rewind(unit, iostat=status)
  if (status /= 0) stop 8
  read(unit, '(I1)', iostat=status) value
  if (status /= 0) stop 9
  if (value /= 7) stop 10
  close(unit, iostat=status)
  if (status /= 0) stop 11
end program
