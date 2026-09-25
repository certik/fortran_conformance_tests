program procedure_reference_c1536_branch_invalid
  implicit none
  call choose(*100)
100 format('not a branch target')
contains
  subroutine choose(*)
    return 1
  end subroutine
end program procedure_reference_c1536_branch_invalid
