program procedure_reference_15_5_1_alt_return
  implicit none
  integer :: branch, checks
  checks = 0
  branch = -1
  call choose(2, *100, *200)
  branch = -99
  go to 900
100 branch = 100
  go to 900
200 branch = 200
  go to 900
300 branch = 300
  go to 900
900 if (branch /= 200) error stop 501
  checks = checks + 1
  if (checks /= 1) error stop 599
  print '(a)', 'PROCEDURE REFERENCE ALTERNATE RETURN OK'
contains
  subroutine choose(which, *, *)
    integer, intent(in) :: which
    if (which == 1) return 1
    return 2
  end subroutine
end program procedure_reference_15_5_1_alt_return
