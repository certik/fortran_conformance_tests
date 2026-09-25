program procedure_reference_c1536_branch_control
  implicit none
  integer :: branch
  branch = -1
  call choose(*100)
  branch = -2
  go to 900
100 branch = 100
900 if (branch /= 100) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1536 BRANCH CONTROL OK'
contains
  subroutine choose(*)
    return 1
  end subroutine
end program procedure_reference_c1536_branch_control
