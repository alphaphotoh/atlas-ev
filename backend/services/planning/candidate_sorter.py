class CandidateSorter:

    @staticmethod
    def sort(candidates):

        candidates.sort(

            key=lambda candidate: candidate.score,

            reverse=True

        )

        return candidates